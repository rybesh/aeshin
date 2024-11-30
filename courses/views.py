from typing import Optional
from .models import Course, Assignment, Submission, User
from django import forms
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import SimpleUploadedFile
from zipfile import ZipFile, BadZipfile
from io import StringIO, BytesIO
import datetime
import csv
import magic
import itertools
import functools


def index(request):
    o = {}
    o["courses"] = Course.objects.order_by("title", "-year", "semester")
    return render(request, "courses.html", context=o)


def course(_, slug):
    courses = list(Course.objects.filter(slug=slug).order_by("-year", "semester"))
    if len(courses) == 0:
        raise Course.DoesNotExist
    return redirect(courses[0])


def info(request, slug, year, semester):
    o = {}
    o["course"] = get_object_or_404(Course, slug=slug, year=year, semester=semester)
    return render(request, "info.html", context=o)


def schedule(request, slug, year, semester):
    o = {}
    o["course"] = get_object_or_404(Course, slug=slug, year=year, semester=semester)
    o["meetings"] = list(o["course"].meetings.all())

    o["milestones"] = o["course"].get_scheduled_items()
    o["in_flux"] = False

    schedule = o["milestones"] + o["meetings"]
    o["schedule"] = sorted(schedule, key=lambda x: (x.date, x.priority))

    today = datetime.date.today()
    need_next = True
    for i, item in enumerate(o["schedule"]):
        if hasattr(item, "is_tentative") and item.is_tentative:
            o["in_flux"] = True
        if need_next and item.date >= today:
            if i > 0:
                item.next = True
            need_next = False
    o["user_is_authorized"] = o["course"].is_authorized(request.user)
    o["unit_counter"] = functools.partial(next, itertools.count(start=1))
    return render(request, "schedule.html", context=o)


def milestones(request, slug, year, semester):
    o = {}
    o["course"] = get_object_or_404(Course, slug=slug, year=year, semester=semester)
    o["milestones"] = o["course"].get_scheduled_items()

    return render(request, "milestones.html", context=o)


def guidelines(request, slug, year, semester):
    o = {}
    o["course"] = get_object_or_404(Course, slug=slug, year=year, semester=semester)
    return render(request, "guidelines.html", context=o)


def assignments(request, slug, year, semester):
    o = {}
    o["course"] = get_object_or_404(Course, slug=slug, year=year, semester=semester)
    return render(request, "assignments.html", context=o)


class SubmissionForm(forms.Form):
    upload = forms.FileField(
        help_text="""
        Please upload either a PDF, or a single zip archive
        containing all the required files for this assignment.
        """
    )


def handleZipUpload(request: HttpRequest, assignment: Assignment, zipfile):
    submission = None
    try:
        submission, new = assignment.submissions.get_or_create(submitter=request.user)
        if not new:
            submission.zipfile.delete(save=False)
        submission.zipfile = zipfile
        submission.save()
        messages.success(request, "Your submission was successfully uploaded.")
    except BadZipfile:
        messages.error(
            request, "The file %s is not a valid zip archive." % zipfile.name
        )
    return submission


def handlePDFUpload(request: HttpRequest, assignment: Assignment, pdf):
    with BytesIO() as buffer:
        with ZipFile(buffer, mode="w") as zip:
            zip.writestr(pdf.name, pdf.read())
        buffer.seek(0)
        return handleZipUpload(
            request,
            assignment,
            SimpleUploadedFile(pdf.name, buffer.read(), content_type="application/zip"),
        )


def handleSubmission(request: HttpRequest, o: dict) -> Optional[Submission]:
    form = SubmissionForm(request.POST, request.FILES)
    submission = None
    if form.is_valid():
        upload = request.FILES["upload"]
        mimetype = magic.from_buffer(upload.read(2048), mime=True)
        upload.seek(0)  # since we read 2K
        if mimetype == "application/zip":
            submission = handleZipUpload(request, o["assignment"], upload)
        elif mimetype == "application/pdf":
            submission = handlePDFUpload(request, o["assignment"], upload)
        else:
            messages.error(
                request, "The file %s is not a PDF or zip archive." % upload.name
            )
    return submission


@login_required
def submit_assignment(request, assignment_id):
    o = {}

    o["assignment"] = get_object_or_404(Assignment, id=assignment_id)
    if not (o["assignment"].is_handed_out and o["assignment"].is_submitted_online):
        raise Http404

    o["course"] = o["assignment"].course
    if not o["course"].is_authorized(request.user):
        return HttpResponseForbidden()

    submission = None
    form = SubmissionForm()

    if request.method == "POST":
        submission = handleSubmission(request, o)

    else:
        submitter = request.user.username
        if request.user.is_superuser and "username" in request.GET:
            submitter = request.GET["username"]
        try:
            submission = o["assignment"].submissions.get(submitter__username=submitter)
        except Submission.DoesNotExist:
            pass

    if submission:
        try:
            o["files"] = [
                f
                for f in ZipFile(submission.zipfile).namelist()
                if not f.startswith("__MACOSX/")
            ]
            o["zipfile_url"] = submission.zipfile.url
        except:  # noqa: E722
            pass

    o["form"] = form
    return render(request, "submit_assignment.html", context=o)


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
    header = ["Name", "Username"]
    for a in assignments:
        header.extend([f"{a.title}|{a.id}|Grade", f"{a.title}|{a.id}|Comment"])
    table = [header]
    for s in course.students.filter(is_active=True).order_by("last_name"):
        row = [s.get_full_name(), s.username]
        for a in assignments:
            try:
                submission = a.submissions.get(submitter=s)
                grade = (
                    submission.letter_grade if a.is_letter_graded else submission.grade
                )
                row.extend([grade, submission.comments])
            except Submission.DoesNotExist:
                row.extend(["", ""])
        table.append(row)
    buf = StringIO()
    csv.writer(buf).writerows(table)
    response = HttpResponse(buf.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="grades.csv"'
    return response


def get_assignment_data(course: Course, assignment: Assignment, student: User) -> dict:
    students = course.students.filter(is_active=True).values_list("username", flat=True)
    data = {"title": assignment.title, "is_graded": assignment.is_graded}
    grades = {}
    for submission in assignment.submissions.all():
        if submission.submitter.username in students:
            grades[submission.submitter.username] = submission.get_grade()
        if submission.submitter == student:
            data["comments"] = submission.comments
            if submission.zipfile:
                data["zipfile_url"] = submission.zipfile.url
    if assignment.is_letter_graded:
        data["grade"] = grades.get(student.username, "")
        data["median"] = "N/A"
    else:
        data["grade"] = "%s / %s" % (
            grades.get(student.username, ""),
            assignment.points,
        )
        data["median"] = "%s / %s" % (median(grades.values()), assignment.points)
    return data


@login_required
def grades(request, slug, year, semester):
    o = {}
    o["course"] = get_object_or_404(Course, slug=slug, year=year, semester=semester)
    if request.user.is_staff:
        if "username" in request.GET:
            o["student"] = get_object_or_404(User, username=request.GET["username"])
        elif "csv" in request.GET:
            return grades_csv(o["course"])
        else:
            o["students"] = (
                o["course"].students.filter(is_active=True).order_by("last_name")
            )
            return render(request, "all-grades.html", context=o)
    elif o["course"].has_student(request.user):
        o["student"] = request.user
    else:
        return HttpResponseForbidden()

    o["assignments"] = []
    for assignment in o["course"].assignments.filter(is_handed_out=True):
        if not (assignment.is_graded or request.user.is_staff):
            continue
        data = get_assignment_data(o["course"], assignment, o["student"])
        o["assignments"].append(data)

    return render(request, "grades.html", context=o)
