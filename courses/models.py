from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from shared import bibutils
from shared.utils import truncate
from django.utils import timezone
from types import SimpleNamespace
from typing import TYPE_CHECKING
import datetime
import re

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


def milestone(date, name, url, passed, description=""):
    m = SimpleNamespace()
    m.date = date
    m.name = name
    m.url = url
    m.passed = passed
    m.description = description
    m.is_milestone = True
    return m


class Department(models.Model):
    name = models.CharField(max_length=80)
    url = models.URLField()

    def __str__(self):
        return self.name


class Instructor(models.Model):
    name = models.CharField(max_length=36)
    url = models.URLField()

    def __str__(self):
        return self.name


class Course(models.Model):
    YEAR_CHOICES = (
        (2011, "2011"),
        (2012, "2012"),
        (2013, "2013"),
        (2014, "2014"),
        (2015, "2015"),
        (2016, "2016"),
        (2017, "2017"),
        (2018, "2018"),
        (2019, "2019"),
        (2020, "2020"),
        (2021, "2021"),
        (2022, "2022"),
        (2023, "2023"),
        (2024, "2024"),
    )
    SEMESTER_CHOICES = (
        ("sp", "Spring"),
        ("fa", "Fall"),
    )
    department = models.ForeignKey(
        "Department", related_name="courses", on_delete=models.PROTECT
    )
    instructors = models.ManyToManyField("Instructor", related_name="courses_teaching")
    students = models.ManyToManyField(User, related_name="courses")
    number = models.CharField(max_length=20)
    slug = models.CharField(max_length=20)
    title = models.CharField(max_length=80)
    semester = models.CharField(max_length=2, choices=SEMESTER_CHOICES)
    year = models.IntegerField(choices=YEAR_CHOICES)
    times = models.CharField(max_length=64)
    location = models.CharField(max_length=256)
    recitations = models.TextField(blank=True)
    description = models.TextField()
    blurb = models.TextField(blank=True)
    evaluation = models.TextField(blank=True)
    participation = models.TextField(blank=True)
    how_to_succeed = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    is_weekly = models.BooleanField(default=False)

    if TYPE_CHECKING:
        meetings = RelatedManager["Meeting"]()
        milestones = RelatedManager["Milestone"]()
        assignments = RelatedManager["Assignment"]()

    def has_student(self, student):
        return len(self.students.filter(id=student.id, is_active=True)) > 0

    def is_authorized(self, user):
        return user.is_staff or self.has_student(user)

    def get_milestones(self):
        milestones = []
        today = datetime.date.today()

        for m in self.milestones.all():
            milestones.append(
                milestone(
                    m.date,
                    m.name,
                    None,
                    today > m.date,
                    m.description,
                )
            )

        for a in self.assignments.filter(due_date__isnull=False):
            milestones.append(
                milestone(
                    a.due_date,
                    f"{a.title}{'' if a.is_inclass else ' due'}",
                    a.get_absolute_url() if a.is_handed_out else None,
                    today > a.due_date,  # type: ignore
                )
            )
            if a.available_date is not None:
                milestones.append(
                    milestone(
                        a.available_date,
                        f"{a.title} handed out",
                        a.get_absolute_url() if a.is_handed_out else None,
                        today > a.available_date,
                    )
                )

        milestones.sort(key=lambda x: x.date)

        return milestones

    def get_absolute_url(self):
        return reverse(
            "course_info_view",
            kwargs={"slug": self.slug, "semester": self.semester, "year": self.year},
        )

    def __str__(self):
        return "%s: %s, %s %s" % (
            self.number,
            self.title,
            self.get_semester_display(),  # type: ignore
            self.get_year_display(),  # type: ignore
        )

    class Meta:
        unique_together = ("slug", "semester", "year")
        ordering = ("-year", "semester")


def upload_slides_to(o, _):
    return "courses/%s/%s/%s/slides/%s.pdf" % (
        o.course.slug,
        o.course.year,
        o.course.semester,
        o.date.strftime("%m-%d"),
    )


class Meeting(models.Model):
    course = models.ForeignKey(
        "Course", related_name="meetings", on_delete=models.PROTECT
    )
    date = models.DateField()
    title = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    readings = models.ManyToManyField(
        "Reading", through="ReadingAssignment", blank=True
    )
    is_tentative = models.BooleanField(default=True)
    slides = models.FileField(upload_to=upload_slides_to, blank=True, null=True)

    is_milestone = False  # for sorting with milestones

    def has_readings(self):
        return len(self.readings.all()) > 0

    def required_reading_list(self):
        return self.readings.filter(readingassignment__is_optional=False).order_by(
            "readingassignment__order"
        )

    def optional_reading_list(self):
        return self.readings.filter(readingassignment__is_optional=True).order_by(
            "readingassignment__order"
        )

    def word_count(self):
        if not self.has_readings():
            return None
        centiwords = 0
        for reading in self.required_reading_list():
            if reading.centiwords:
                centiwords += reading.centiwords
        if centiwords > 0:
            return "{:,}".format(centiwords * 100)
        else:
            return None

    def __str__(self):
        return "%s: %s" % (self.date.strftime("%m-%d"), self.title)

    class Meta:
        ordering = ("course", "date")


class Unit(models.Model):
    course = models.ForeignKey("Course", related_name="units", on_delete=models.PROTECT)
    starts_with = models.OneToOneField(
        "Meeting", related_name="starts_unit", on_delete=models.PROTECT
    )
    title = models.CharField(max_length=80)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Milestone(models.Model):
    course = models.ForeignKey(
        "Course", related_name="milestones", on_delete=models.CASCADE
    )
    date = models.DateField()
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)

    def __str__(self):
        return "%s: %s" % (self.date.strftime("%m-%d"), self.name)

    class Meta:
        ordering = ("date",)


class Assignment(models.Model):
    id = models.AutoField(primary_key=True)
    course = models.ForeignKey(
        "Course", related_name="assignments", on_delete=models.CASCADE
    )
    slug = models.SlugField()
    due_date = models.DateField(null=True, blank=True)
    available_date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=80)
    description = models.TextField()
    points = models.IntegerField(default=0)
    is_handed_out = models.BooleanField(default=False)
    is_submitted_online = models.BooleanField(default=False)
    is_letter_graded = models.BooleanField(default=False)
    is_graded = models.BooleanField("has been graded", default=False)
    is_inclass = models.BooleanField("given in class", default=False)

    if TYPE_CHECKING:
        submissions = RelatedManager["Submission"]()

    def get_absolute_url(self):
        return (
            reverse(
                "course_assignments_view",
                kwargs={
                    "slug": self.course.slug,
                    "semester": self.course.semester,
                    "year": self.course.year,
                },
            )
            + "#"
            + self.slug
        )

    def get_submit_url(self):
        return reverse(
            "course_submit_assignment_view", kwargs={"assignment_id": self.id}
        )

    def was_submitted_by(self, user):
        try:
            self.submissions.get(submitter=user)
            return True
        except Submission.DoesNotExist:
            return False

    def __str__(self):
        if self.due_date:
            return "%s %s: %s" % (
                self.course.number,
                self.due_date.strftime("%m-%d"),
                self.title,
            )
        else:
            return "%s: %s" % (self.course.number, self.title)

    class Meta:
        ordering = ("due_date", "slug")


def submission_upload_to(o, _):
    return "courses/%s/%s/%s/assignments/%s/%s.zip" % (
        o.assignment.course.slug,
        o.assignment.course.year,
        o.assignment.course.semester,
        o.assignment.slug,
        o.submitter.username,
    )


class Submission(models.Model):
    assignment = models.ForeignKey(
        "Assignment", related_name="submissions", on_delete=models.PROTECT
    )
    submitter = models.ForeignKey(
        User, related_name="submissions", on_delete=models.PROTECT
    )
    time_submitted = models.DateTimeField()
    zipfile = models.FileField(upload_to=submission_upload_to, blank=True)
    grade = models.FloatField(default=0.0)
    letter_grade = models.CharField(blank=True, max_length=16)
    comments = models.TextField(blank=True)

    def get_grade(self):
        return self.letter_grade or self.grade

    def save(self, *args, **kwargs):
        self.time_submitted = timezone.now()
        super(Submission, self).save(*args, **kwargs)

    def __str__(self):
        return "%s: %s" % (self.assignment, self.submitter)


PROXY = "http://libproxy.lib.unc.edu/login?url="


class Linky:
    def __init__(self, stored_url, access_via_proxy, ignore_citation_url):
        self.url = ""
        self.stored_url = stored_url
        self.access_via_proxy = access_via_proxy
        self.ignore_citation_url = ignore_citation_url

    def linkify(self, html):
        html = re.sub(r" (https?://.+)\.", self.repl, html, 1)
        if self.stored_url and not self.url == self.stored_url:
            if self.access_via_proxy:
                anchor = self.stored_url[len(PROXY) :]
            elif self.stored_url.startswith("/"):
                anchor = self.stored_url.split(".")[-1].upper()
            else:
                anchor = self.stored_url
            html = re.sub(
                r"</div>\n</div>",
                r' <a target="_blank" href="%s">%s</a>.</div>\n</div>'
                % (self.stored_url, anchor),
                html,
                1,
            )
        return mark_safe(html)

    def repl(self, match):
        if self.ignore_citation_url:
            return ""
        self.url = match.group(1)
        if self.access_via_proxy:
            self.url = PROXY + self.url
        return ' <a target="_blank" href="%s">%s</a>.' % (self.url, match.group(1))


class Reading(models.Model):
    zotero_id = models.CharField(max_length=16)
    citation_text = models.CharField(max_length=128, blank=True, editable=False)
    citation_html = models.TextField(blank=True, editable=False)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="courses/readings", blank=True)
    url = models.URLField(blank=True)
    access_via_proxy = models.BooleanField(default=False)
    ignore_citation_url = models.BooleanField(default=False)
    centiwords = models.PositiveSmallIntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.zotero_id:
            self.citation_text = bibutils.format_zotero_as_text(self.zotero_id)
            self.citation_html = bibutils.format_zotero_as_html(self.zotero_id)
        super(Reading, self).save(*args, **kwargs)

    def get_url(self):
        if self.file:
            return self.file.url
        if self.url:
            if self.access_via_proxy:
                return PROXY + self.url
            else:
                return self.url
        return ""

    def as_html(self):
        linky = Linky(self.get_url(), self.access_via_proxy, self.ignore_citation_url)
        unstyled_html = re.sub(r'style="[^"]+"', "", self.citation_html)
        return linky.linkify(unstyled_html)

    def word_count(self):
        if not self.centiwords:
            return None
        return "{:,}".format(self.centiwords * 100)

    def __str__(self):
        return truncate(self.citation_text)

    class Meta:
        ordering = ("citation_text",)


class ReadingAssignment(models.Model):
    id = models.AutoField(primary_key=True)
    meeting = models.ForeignKey(
        "Meeting", related_name="reading_assignments", on_delete=models.CASCADE
    )
    reading = models.ForeignKey("Reading", on_delete=models.PROTECT)
    order = models.IntegerField(blank=True, null=True)
    is_optional = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse("course_discussion_view", kwargs={"discussion_id": self.id})

    class Meta:
        ordering = ("order",)
