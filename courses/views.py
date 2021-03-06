from .models import Course, Assignment, ReadingAssignment, Submission, User
from .models import PeerReview, PeerReviewSession
from django import forms
from django.http import HttpResponse, HttpResponseForbidden, FileResponse
from django.http import HttpResponseRedirect, HttpResponseServerError, Http404
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Count
from zipfile import ZipFile, BadZipfile
from io import StringIO, BytesIO
import datetime
import csv
import magic
import random
import itertools
import functools


def index(request):
    o = {}
    o['courses'] = Course.objects.order_by('title', '-year', 'semester')
    return render(request, 'courses.html', context=o)


def info(request, slug, year, semester):
    o = {}
    o['course'] = get_object_or_404(
        Course, slug=slug, year=year, semester=semester)
    return render(request, 'info.html', context=o)


def schedule(request, slug, year, semester):
    o = {}
    o['course'] = get_object_or_404(
        Course, slug=slug, year=year, semester=semester)
    o['meetings'] = list(o['course'].meetings.all())

    o['milestones'] = o['course'].get_milestones()
    o['in_flux'] = False

    schedule = o['milestones'] + o['meetings']
    o['schedule'] = sorted(schedule, key=lambda x: (x.date, x.is_milestone))

    today = datetime.date.today()
    need_next = True
    for i, item in enumerate(o['schedule']):
        if hasattr(item, 'is_tentative') and item.is_tentative:
            o['in_flux'] = True
        if need_next and item.date >= today:
            if i > 0:
                item.next = True
            need_next = False
    o['user_is_authorized'] = o['course'].is_authorized(request.user)
    o['unit_counter'] = functools.partial(next, itertools.count(start=1))
    return render(request, 'schedule.html', context=o)


def milestones(request, slug, year, semester):
    o = {}
    o['course'] = get_object_or_404(
        Course, slug=slug, year=year, semester=semester)
    o['milestones'] = o['course'].get_milestones()

    return render(request, 'milestones.html', context=o)


def guidelines(request, slug, year, semester):
    o = {}
    o['course'] = get_object_or_404(
        Course, slug=slug, year=year, semester=semester)
    return render(request, 'guidelines.html', context=o)


def thanks(request, slug, year, semester):
    o = {}
    o['course'] = get_object_or_404(
        Course, slug=slug, year=year, semester=semester)
    return render(request, 'thanks.html', context=o)


def assignments(request, slug, year, semester):
    o = {}
    o['course'] = get_object_or_404(
        Course, slug=slug, year=year, semester=semester)
    return render(request, 'assignments.html', context=o)


class SubmissionForm(forms.Form):
    upload = forms.FileField(
        help_text='''
        Please upload a either a PDF, or a single zip archive
        containing all the required files for this assignment.
        '''
    )


def handleZipUpload(request, assignment, zipfile):
    submission = None
    try:
        submission, new = assignment.submissions.get_or_create(
            submitter=request.user)
        if not new:
            submission.zipfile.delete(save=False)
        submission.zipfile = zipfile
        submission.save()
        messages.success(
            request, 'Your submission was successfully uploaded.')
    except BadZipfile:
        messages.error(
            request, 'The file %s is not a valid zip archive.'
            % zipfile.name)
    return submission


def handlePDFUpload(request, assignment, pdf):
    with BytesIO() as buffer:
        with ZipFile(buffer, mode='w') as zip:
            zip.writestr(pdf.name, pdf.read())
        buffer.seek(0)
        return handleZipUpload(request, assignment, SimpleUploadedFile(
            pdf.name, buffer.read(), content_type='application/zip'))


@login_required
def submit_assignment(request, assignment_id):
    o = {}

    o['assignment'] = get_object_or_404(Assignment, id=assignment_id)
    if not (o['assignment'].is_handed_out
            and o['assignment'].is_submitted_online):
        raise Http404

    o['course'] = o['assignment'].course
    if not o['course'].is_authorized(request.user):
        return HttpResponseForbidden()

    submission = None

    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            upload = request.FILES['upload']
            mimetype = magic.from_buffer(upload.read(2048), mime=True)
            upload.seek(0)  # since we read 2K
            if mimetype == 'application/zip':
                submission = handleZipUpload(request, o['assignment'], upload)
            elif mimetype == 'application/pdf':
                submission = handlePDFUpload(request, o['assignment'], upload)
            else:
                messages.error(
                    request, 'The file %s is not a PDF or zip archive.'
                    % upload.name)

    else:
        form = SubmissionForm()
        submitter = request.user.username
        if request.user.is_superuser and 'username' in request.GET:
            submitter = request.GET['username']
        try:
            submission = o['assignment'].submissions.get(
                submitter__username=submitter)
        except Submission.DoesNotExist:
            pass

    if submission:
        try:
            o['files'] = [f for f in ZipFile(submission.zipfile).namelist()
                          if not f.startswith('__MACOSX/')]
            o['zipfile_url'] = submission.zipfile.url
        except:  # noqa: E722
            pass

    o['form'] = form
    return render(request, 'submit_assignment.html', context=o)


@login_required
def review_assignment(request, assignment_id):

    assignment = get_object_or_404(Assignment, id=assignment_id)
    if not (assignment.is_handed_out
            and assignment.is_submitted_online):
        raise Http404

    if not assignment.course.is_authorized(request.user):
        return HttpResponseForbidden(
            'You are not a student in this class.')

    if not (request.user.is_staff
            or assignment.was_submitted_by(request.user)):
        return HttpResponseForbidden(
            'You have not submitted this assignment yet.')

    review = None

    try:
        session = assignment.peer_review_session

        if not (session.active or request.user.is_staff):
            return HttpResponseForbidden('This peer review session has ended.')

        review = session.reviews.get(
            reviewer=request.user, state=PeerReview.IN_PROGRESS)

    except PeerReviewSession.DoesNotExist:
        raise Http404
    except PeerReview.MultipleObjectsReturned:
        # ruh roh
        return HttpResponseServerError()
    except PeerReview.DoesNotExist:
        pass

    if review is None:
        # check for pre-created reviews (e.g. for late submissions)
        new_reviews = list(
            session.reviews.filter(reviewer=request.user, state=PeerReview.NEW)
        )
        review = random.choice(new_reviews) if len(new_reviews) > 0 else None

        if review is not None:
            review.state = PeerReview.IN_PROGRESS
            review.save()

    if review is None:
        submissions = (assignment
                       .submissions
                       .exclude(submitter=request.user)
                       .exclude(under_review=True)
                       .annotate(review_count=Count('reviews')))

        unreviewed = list(submissions.filter(review_count=0))
        reviewed = list(submissions.filter(review_count__gt=0))

        submission = random.choice(unreviewed) if len(unreviewed) > 0 else None
        if submission is None:
            submission = random.choice(reviewed) if len(reviewed) > 0 else None

        if submission is not None:
            review = session.new_review_or_none(submission, request.user)

    return render(request, 'review_assignment.html', context={
        'submitted': 'submitted' in request.GET,
        'course': assignment.course,
        'assignment': assignment,
        'review': review,
        'grader': request.user.is_staff,
        'GRADE_CHOICES': PeerReview.GRADE_CHOICES,
    })


def validate_review(review, user):
    if not review.reviewer == user:
        return (False,
                'You are not authorized to access this submission.')
    if review.state == PeerReview.NEW:
        return (False,
                'This review has not yet begun.')
    if review.state == PeerReview.COMPLETE:
        return (False,
                'This review has already been submitted.')
    if not (review.session.active or user.is_staff):
        return (False,
                'This peer review session has ended.')
    return (True, '')


@login_required
def download_reviewed_submission(request, review_id):
    review = get_object_or_404(PeerReview, id=review_id)

    is_valid, msg = validate_review(review, request.user)

    if is_valid:
        return FileResponse(
            review.submission.zipfile,
            filename='under-review-%s.zip' % review_id,
            as_attachment=True)

    else:
        return HttpResponseForbidden(msg)


@login_required
def submit_review(request, review_id):
    if not request.method == 'POST':
        raise Http404

    review = get_object_or_404(PeerReview, id=review_id)

    is_valid, msg = validate_review(review, request.user)

    if is_valid:
        review.suggested_grade = request.POST.get(
            'suggested-grade', PeerReview.NONE)
        review.submit()
        return HttpResponseRedirect('%s?submitted' % review.session.get_url())
    else:
        return HttpResponseForbidden(msg)


def get_current_course(slug):
    courses = list(Course.objects.filter(blog_slug=slug).order_by('id'))
    if len(courses) == 0:
        raise Course.DoesNotExist
    return courses[-1]


def median(pool):
    if len(pool) == 0:
        return None
    copy = sorted(pool)
    size = len(copy)
    if size % 2 == 1:
        return copy[int((size - 1) / 2)]
    else:
        return (copy[int(size / 2 - 1)] + copy[int(size / 2)]) / 2


def grades_csv(course):
    assignments = course.assignments.filter(is_graded=True)
    table = [['Name', 'Username']
             + [a.title for a in assignments]
             + ['Extra credit']]
    for s in course.students.filter(is_active=True).order_by('last_name'):
        row = [s.get_full_name(), s.username]
        for a in assignments:
            try:
                submission = a.submissions.get(submitter=s)
                grade = (submission.letter_grade if a.is_letter_graded
                         else submission.grade)
                row.append(grade)
            except Submission.DoesNotExist:
                row.append('')
        table.append(row)
    buf = StringIO()
    csv.writer(buf).writerows(table)
    response = HttpResponse(buf.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="grades.csv"'
    return response


@login_required
def grades(request, slug, year, semester):
    o = {}
    o['course'] = get_object_or_404(
        Course, slug=slug, year=year, semester=semester)
    if request.user.is_staff:
        if 'username' in request.GET:
            o['student'] = get_object_or_404(
                User, username=request.GET['username'])
        elif 'csv' in request.GET:
            return grades_csv(o['course'])
        else:
            o['students'] = (o['course'].students
                             .filter(is_active=True).order_by('last_name'))
            return render(request, 'all-grades.html', context=o)
    elif o['course'].has_student(request.user):
        o['student'] = request.user
    else:
        return HttpResponseForbidden()
    students = o['course'].students\
        .filter(is_active=True)\
        .values_list('username', flat=True)
    counts = {}

    def setdefault(username):
        return counts.setdefault(username, {
            'discussion_count': 0, 'post_count': 0, 'comment_count': 0})
    for leader in ReadingAssignment.objects\
            .filter(meeting__course=o['course'])\
            .values_list('discussion_leader__username', flat=True):
        if leader in students:
            setdefault(leader)['discussion_count'] += 1
    o['discussion_count'] = setdefault(
        o['student'].username)['discussion_count']
    o['discussion_median'] = median(
        [v['discussion_count'] for v in counts.values()])
    o['assignments'] = []
    for assignment in o['course'].assignments.filter(
            is_handed_out=True, is_graded=True
    ):
        grades = {}
        data = {'title': assignment.title}
        for submission in assignment.submissions.all():
            if submission.submitter.username in students:
                grades[submission.submitter.username] = submission.get_grade()
            if submission.submitter == o['student']:
                data['comments'] = submission.comments
                if submission.zipfile:
                    data['zipfile_url'] = submission.zipfile.url
        if assignment.is_letter_graded:
            data['grade'] = grades.get(o['student'].username, '')
            data['median'] = 'N/A'
        else:
            data['grade'] = '%s / %s' % (
                grades.get(o['student'].username, ''), assignment.points)
            data['median'] = '%s / %s' % (
                median(grades.values()), assignment.points)
        o['assignments'].append(data)

    return render(request, 'grades.html', context=o)
