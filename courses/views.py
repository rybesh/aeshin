from .models import Course, Assignment, ReadingAssignment, Submission, User
from django import forms
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import SimpleUploadedFile
from zipfile import ZipFile, BadZipfile
from io import StringIO
import datetime
import csv
import magic


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
    o['holidays'] = list(o['course'].holidays.all())
    assignments = {}
    for i, assignment in enumerate(
            o['course'].assignments.filter(due_date__isnull=False)
    ):
        assignment.number = (i + 1)
        assignments_due = assignments.get(assignment.due_date, [])
        assignments_due.append(assignment)
        assignments[assignment.due_date] = assignments_due
    o['in_flux'] = False
    o['schedule'] = o['meetings'] + o['holidays']
    o['schedule'].sort(key=lambda x: x.date)
    today = datetime.date.today()
    for item in o['schedule']:
        item.assignments_due = assignments.get(item.date, [])
        if hasattr(item, 'is_tentative') and item.is_tentative:
            o['in_flux'] = True
        if item.date >= today:
            item.next = True
    o['user_is_authorized'] = o['course'].is_authorized(request.user)
    return render(request, 'schedule.html', context=o)


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
        help_text='Please upload a either a PDF, or a single zip archive'
        + ' containing all the required files for this assignment.')


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
    buffer = StringIO()
    with ZipFile(buffer, mode='w') as zip:
        zip.writestr(pdf.name, pdf.read())
    buffer.seek(0)
    return handleZipUpload(request, assignment, SimpleUploadedFile(
        pdf.name, buffer.read(), content_type='application/zip'))


@login_required
def submit_assignment(request, assignment_id):
    o = {}

    o['assignment'] = get_object_or_404(Assignment, id=assignment_id)
    if not (o['assignment'].is_handed_out and
            o['assignment'].is_submitted_online):
        raise Http404

    o['course'] = o['assignment'].course
    if not o['course'].is_authorized(request.user):
        return HttpResponseForbidden()

    submission = None

    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            upload = request.FILES['upload']
            mimetype = magic.from_buffer(upload.read(1024), mime=True)
            print(mimetype)
            upload.seek(0)  # since we read 1K
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
        except:
            pass

    o['form'] = form
    return render(request, 'submit_assignment.html', context=o)


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
        return copy[(size - 1) / 2]
    else:
        return (copy[size/2 - 1] + copy[size/2]) / 2


def grades_csv(course):
    assignments = course.assignments.filter(is_graded=True)
    table = [['Name'] + [a.title for a in assignments]]
    for s in course.students.filter(is_active=True):
        row = [s.get_full_name()]
        for a in assignments:
            try:
                row.append(a.submissions.get(submitter=s).grade)
            except Submission.DoesNotExist:
                row.append('')
        table.append(row)
    buf = StringIO()
    csv.writer(buf).writerows(table)
    return HttpResponse(buf.getvalue(), 'text/csv')


@login_required
def grades(request, slug, year, semester):
    o = {}
    o['course'] = get_object_or_404(
        Course, slug=slug, year=year, semester=semester)
    if request.user.is_superuser:
        if 'username' in request.GET:
            o['student'] = get_object_or_404(
                User, username=request.GET['username'])
        else:
            return grades_csv(o['course'])
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
