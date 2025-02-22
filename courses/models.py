import json
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry, CHANGE
from django.core.files.storage import FileSystemStorage
from django.utils.safestring import mark_safe
from shared import bibutils
from shared.templatetags.markdown import markdown
from shared.utils import truncate
from django.utils import timezone
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass
import datetime
import re

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


class Department(models.Model):
    name = models.CharField(max_length=80)
    url = models.URLField()

    def __str__(self):
        return self.name


class Building(models.Model):
    name = models.CharField(max_length=80)
    url = models.URLField()

    def __str__(self):
        return self.name


class Instructor(models.Model):
    name = models.CharField(max_length=36)
    url = models.URLField()

    def __str__(self):
        return self.name


@dataclass
class Scheduled:
    date: datetime.date
    date_range: str
    name: str
    passed: bool
    url: Optional[str] = None
    description: str = ""
    is_milestone: bool = True
    priority: int = 1


class ExternalCourse(models.Model):
    YEAR_CHOICES = (
        (2025, "2025"),
        (2026, "2026"),
        (2027, "2027"),
    )
    SEMESTER_CHOICES = (
        ("sp", "Spring"),
        ("fa", "Fall"),
    )
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=80)
    subtitle = models.CharField(max_length=80, blank=True)
    blurb = models.TextField(blank=True)
    semester = models.CharField(max_length=2, choices=SEMESTER_CHOICES)
    year = models.IntegerField(choices=YEAR_CHOICES)
    url = models.URLField()

    def get_absolute_url(self):
        return self.url

    def __str__(self):
        return "%s, %s %s" % (
            self.title,
            self.get_semester_display(),  # type: ignore
            self.get_year_display(),  # type: ignore
        )


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
        (2025, "2025"),
        (2026, "2026"),
        (2027, "2027"),
    )
    SEMESTER_CHOICES = (
        ("sp", "Spring"),
        ("fa", "Fall"),
    )
    id = models.AutoField(primary_key=True)
    department = models.ForeignKey(
        "Department", related_name="courses", on_delete=models.PROTECT
    )
    building = models.ForeignKey(
        "Building", on_delete=models.PROTECT, null=True, blank=True
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
    room = models.CharField(max_length=20, blank=True)
    description = models.TextField()
    blurb = models.TextField(blank=True)
    evaluation = models.TextField(blank=True)
    participation = models.TextField(blank=True)
    communication = models.TextField(blank=True)
    how_to_succeed = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    is_weekly = models.BooleanField(default=False)
    slides_are_called_notes = models.BooleanField(default=False)
    zulip_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)

    if TYPE_CHECKING:
        meetings = RelatedManager["Meeting"]()
        milestones = RelatedManager["Milestone"]()
        assignments = RelatedManager["Assignment"]()

    def has_student(self, student):
        return len(self.students.filter(id=student.id, is_active=True)) > 0

    def is_authorized(self, user):
        return user.is_staff or self.has_student(user)

    def get_time_and_location(self) -> str:
        if self.building and self.room:
            return mark_safe(
                f'<p>{self.times}<br><a target="_blank" href="{self.building.url}">{self.building.name}</a> {self.room}</p>'
            )
        else:
            return mark_safe(markdown(f"{self.times}<br>{self.location}"))

    def get_scheduled_items(self):
        items = []
        today = datetime.date.today()

        for m in self.milestones.all():
            items.append(
                Scheduled(
                    m.date,
                    m.get_date_range(),
                    m.name,
                    today > m.date,
                    description=m.description,
                    priority=0,
                )
            )

        for a in self.assignments.filter(due_date__isnull=False):
            assert a.due_date is not None
            items.append(
                Scheduled(
                    a.due_date,
                    a.due_date.strftime("%B %-d"),
                    f"{a.title}{'' if a.is_inclass else ' due'}",
                    today > a.due_date,
                    a.get_absolute_url() if a.is_handed_out else None,
                    priority=2,
                )
            )
            if a.available_date is not None:
                items.append(
                    Scheduled(
                        a.available_date,
                        a.available_date.strftime("%B %-d"),
                        f"{a.title} handed out",
                        today > a.available_date,
                        a.get_absolute_url() if a.is_handed_out else None,
                        priority=2,
                    )
                )

        items.sort(key=lambda x: x.date)

        return items

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


class Recitation(models.Model):
    course = models.ForeignKey(
        "Course", related_name="recitations", on_delete=models.PROTECT
    )
    building = models.ForeignKey(
        "Building", on_delete=models.PROTECT, null=True, blank=True
    )
    instructor = models.ForeignKey("Instructor", on_delete=models.PROTECT)
    times = models.CharField(max_length=64)
    number = models.CharField(max_length=20)
    room = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.number} ({self.instructor})"


def upload_slides_to(o, _):
    return "courses/%s/%s/%s/slides/%s.pdf" % (
        o.course.slug,
        o.course.year,
        o.course.semester,
        o.date.strftime("%m-%d"),
    )


def upload_pptx_to(o, _):
    return "courses/%s/%s/%s/slides/%s.pptx" % (
        o.course.slug,
        o.course.year,
        o.course.semester,
        o.date.strftime("%m-%d"),
    )


class FileSystemOverwriteStorage(FileSystemStorage):
    """replace files instead of creating new ones"""

    def get_available_name(self, name, max_length=None):
        self.delete(name)
        return super().get_available_name(name, max_length)


class Meeting(models.Model):
    id = models.AutoField(primary_key=True)
    course = models.ForeignKey(
        "Course", related_name="meetings", on_delete=models.PROTECT
    )
    date = models.DateField()
    title = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    readings = models.ManyToManyField(
        "Reading", through="ReadingAssignment", blank=True
    )
    viewings = models.ManyToManyField(
        "Viewing", through="ViewingAssignment", blank=True
    )
    is_tentative = models.BooleanField(default=True)
    slides = models.FileField(upload_to=upload_slides_to, blank=True, null=True)
    powerpoint = models.FileField(
        upload_to=upload_pptx_to,
        storage=FileSystemOverwriteStorage(),
        blank=True,
        null=True,
    )
    priority = 1  # sorting order in schedule

    def has_readings(self):
        return len(self.readings.all()) > 0

    def has_viewings(self):
        return len(self.viewings.all()) > 0

    def required_reading_list(self):
        return self.readings.filter(readingassignment__is_optional=False).order_by(
            "readingassignment__order"
        )

    def optional_reading_list(self):
        return self.readings.filter(readingassignment__is_optional=True).order_by(
            "readingassignment__order"
        )

    def required_viewing_list(self):
        return self.viewings.filter(viewingassignment__is_optional=False).order_by(
            "viewingassignment__order"
        )

    def optional_viewing_list(self):
        return self.viewings.filter(viewingassignment__is_optional=True).order_by(
            "viewingassignment__order"
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

    def minute_count(self):
        if not self.has_viewings():
            return None
        minutes = 0
        for viewing in self.required_viewing_list():
            minutes += viewing.minutes()
        if minutes > 0:
            return "{}".format(minutes)
        else:
            return None

    def slides_updated_at(self) -> datetime.datetime:
        if self.slides:
            updates = LogEntry.objects.filter(
                object_id=self.id,
                action_flag=CHANGE,
            ).order_by("-action_time")
            for update in updates:
                if update.change_message:
                    try:
                        data = json.loads(update.change_message)
                        if "Slides" in data[0]["changed"]["fields"]:
                            return update.action_time
                    except:
                        pass
        return datetime.datetime.now()

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
    end_date = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)

    def get_date_range(self):
        s = self.date.strftime("%B %-d")
        if self.end_date:
            if self.date.month == self.end_date.month:
                return f"{s}–{self.end_date.strftime('%-d')}"
            else:
                return f"{s}–{self.end_date.strftime('%B %-d')}"
        else:
            return s

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
        html = re.sub(r" (https?://.+)\.", self.repl, html, count=1)
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
                count=1,
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


class Viewing(models.Model):
    description = models.TextField()
    tips = models.TextField(blank=True)

    if TYPE_CHECKING:
        parts = RelatedManager["ViewingPart"]()

    def has_multiple_parts(self):
        return len(self.parts.all()) > 1

    def minutes(self) -> int:
        minutes = 0
        for part in self.parts.all():
            if part.minutes:
                minutes += part.minutes
        return minutes

    def minute_count(self) -> str | None:
        minutes = self.minutes()
        if minutes == 0:
            return None
        return "{}".format(minutes)

    def __str__(self):
        return self.description


class ViewingPart(models.Model):
    viewing = models.ForeignKey(
        "Viewing", related_name="parts", on_delete=models.CASCADE
    )
    order = models.PositiveSmallIntegerField()
    minutes = models.PositiveSmallIntegerField()
    url = models.URLField()

    def __str__(self):
        return self.url

    class Meta:
        ordering = ("order",)


class ViewingAssignment(models.Model):
    id = models.AutoField(primary_key=True)
    meeting = models.ForeignKey(
        "Meeting", related_name="viewing_assignments", on_delete=models.CASCADE
    )
    viewing = models.ForeignKey("Viewing", on_delete=models.PROTECT)
    order = models.IntegerField(blank=True, null=True)
    is_optional = models.BooleanField(default=False)

    class Meta:
        ordering = ("order",)
