from django.db import models, transaction
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from shared import bibutils
from shared.utils import truncate
from django.utils import timezone
from types import SimpleNamespace
import datetime
import re


def milestone(date, name, url, passed, description=''):
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
        (2011, '2011'),
        (2012, '2012'),
        (2013, '2013'),
        (2014, '2014'),
        (2015, '2015'),
        (2016, '2016'),
        (2017, '2017'),
        (2018, '2018'),
        (2019, '2019'),
        (2020, '2020'),
        (2021, '2021'),
        (2022, '2022'),
        (2023, '2023'),
        (2024, '2024'),
    )
    SEMESTER_CHOICES = (
        ('sp', 'Spring'),
        ('fa', 'Fall'),
    )
    department = models.ForeignKey(
        'Department', related_name='courses', on_delete=models.PROTECT)
    instructors = models.ManyToManyField(
        'Instructor', related_name='courses_teaching')
    students = models.ManyToManyField(User, related_name='courses')
    number = models.CharField(max_length=20)
    slug = models.CharField(max_length=20)
    title = models.CharField(max_length=80)
    semester = models.CharField(max_length=2, choices=SEMESTER_CHOICES)
    year = models.IntegerField(choices=YEAR_CHOICES)
    times = models.CharField(max_length=64)
    location = models.CharField(max_length=128)
    recitations = models.TextField(blank=True)
    ereserves_id = models.CharField(max_length=8, blank=True)
    description = models.TextField()
    blurb = models.TextField(blank=True)
    evaluation = models.TextField(blank=True)
    participation = models.TextField(blank=True)
    how_to_succeed = models.TextField(blank=True)
    thanks = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    is_weekly = models.BooleanField(default=False)
    blog_slug = models.CharField(max_length=20, blank=True)
    forum = models.URLField(blank=True)

    def has_blog(self):
        return (len(self.blog_slug) > 0)

    def has_forum(self):
        return (len(self.forum) > 0)

    def has_student(self, student):
        return (len(self.students.filter(id=student.id, is_active=True)) > 0)

    def is_authorized(self, user):
        return user.is_staff or self.has_student(user)

    def get_date_range(self):
        if self.semester == 'sp':
            start_day = 1
            start_month = 1
            end_day = 30
            end_month = 4
        elif self.semester == 'fa':
            start_day = 1
            start_month = 8
            end_day = 31
            end_month = 12
        else:  # summer
            start_day = 1
            start_month = 5
            end_day = 31
            end_month = 7
        return (datetime.date(self.year, start_month, start_day),
                datetime.date(self.year, end_month, end_day))

    def get_milestones(self):
        milestones = []
        today = datetime.date.today()

        for m in self.milestones.all():
            milestones.append(milestone(
                m.date,
                m.name,
                None,
                today > m.date,
                m.description,
            ))

        for a in self.assignments.filter(due_date__isnull=False):
            milestones.append(milestone(
                a.due_date,
                f"{a.title} due",
                a.get_absolute_url() if a.is_handed_out else None,
                today > a.due_date
            ))
            if a.available_date is not None:
                a.available_date,
                f"{a.title} handed out",
                a.get_absolute_url() if a.is_handed_out else None,
                today > a.available_date

        milestones.sort(key=lambda x: x.date)

        return milestones

    def get_absolute_url(self):
        return reverse('course_info_view', kwargs={
            'slug': self.slug,
            'semester': self.semester,
            'year': self.year})

    def __str__(self):
        return u'%s: %s, %s %s' % (
            self.number, self.title,
            self.get_semester_display(), self.get_year_display())

    class Meta:
        unique_together = ('slug', 'semester', 'year')
        ordering = ('-year', 'semester')


def upload_to(o, filename):
    return 'courses/%s/%s/%s/slides/%s.pdf' % (
        o.course.slug,
        o.course.year,
        o.course.semester,
        o.date.strftime('%m-%d'))


class Meeting(models.Model):
    course = models.ForeignKey(
        'Course', related_name='meetings', on_delete=models.PROTECT)
    date = models.DateField()
    title = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    readings = models.ManyToManyField(
        'Reading', through='ReadingAssignment', blank=True)
    is_tentative = models.BooleanField(default=True)
    slides = models.FileField(upload_to=upload_to, blank=True, null=True)

    def has_readings(self):
        return len(self.readings.all()) > 0

    def has_ereserves(self):
        for reading in self.readings.all():
            if reading.access_via_ereserves:
                return True
        return False

    def reading_list(self):
        return self.readings.all().order_by('readingassignment__order')

    def required_reading_list(self):
        return self.readings.\
            filter(readingassignment__is_optional=False).\
            order_by('readingassignment__order')

    def optional_reading_list(self):
        return self.readings.\
            filter(readingassignment__is_optional=True).\
            order_by('readingassignment__order')

    def word_count(self):
        if not self.has_readings():
            return None
        centiwords = 0
        for reading in self.required_reading_list():
            if not reading.centiwords:
                return None
            centiwords += reading.centiwords
        return '{:,}'.format(centiwords * 100)

    def __str__(self):
        return u'%s: %s' % (self.date.strftime('%m-%d'), self.title)

    class Meta:
        ordering = ('course', 'date')


class Unit(models.Model):
    course = models.ForeignKey(
        'Course', related_name='units', on_delete=models.PROTECT)
    starts_with = models.OneToOneField(
        'Meeting', related_name='starts_unit', on_delete=models.PROTECT)
    title = models.CharField(max_length=80)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Milestone(models.Model):
    course = models.ForeignKey(
        'Course', related_name='milestones', on_delete=models.CASCADE)
    date = models.DateField()
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)

    def __str__(self):
        return u'%s: %s' % (self.date.strftime('%m-%d'), self.name)

    class Meta:
        ordering = ('date',)


class Assignment(models.Model):
    course = models.ForeignKey(
        'Course', related_name='assignments', on_delete=models.CASCADE)
    slug = models.SlugField()
    due_date = models.DateField(null=True, blank=True)
    available_date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=80)
    description = models.TextField()
    points = models.IntegerField(default=0)
    is_handed_out = models.BooleanField(default=False)
    is_submitted_online = models.BooleanField(default=False)
    is_letter_graded = models.BooleanField(default=False)
    is_graded = models.BooleanField('has been graded', default=False)

    def get_absolute_url(self):
        return (reverse('course_assignments_view', kwargs={
            'slug': self.course.slug,
            'semester': self.course.semester,
            'year': self.course.year}) + '#' + self.slug)

    def get_submit_url(self):
        return (reverse('course_submit_assignment_view', kwargs={
            'assignment_id': self.id}))

    def get_review_url(self):
        return (reverse('course_review_assignment_view', kwargs={
            'assignment_id': self.id}))

    def is_being_peer_reviewed(self):
        try:
            session = self.peer_review_session
            return (session is not None and session.active)
        except PeerReviewSession.DoesNotExist:
            return False

    def was_submitted_by(self, user):
        try:
            self.submissions.get(submitter=user)
            return True
        except Submission.DoesNotExist:
            return False

    def __str__(self):
        if self.due_date:
            return u'%s %s: %s' % (
                self.course.number, self.due_date.strftime('%m-%d'), self.title
            )
        else:
            return u'%s: %s' % (self.course.number, self.title)

    class Meta:
        ordering = ('due_date', 'slug')


def submission_upload_to(o, _):
    return 'courses/%s/%s/%s/assignments/%s/%s.zip' % (
        o.assignment.course.slug,
        o.assignment.course.year,
        o.assignment.course.semester,
        o.assignment.slug,
        o.submitter.username)


class Submission(models.Model):
    assignment = models.ForeignKey(
        'Assignment', related_name='submissions', on_delete=models.PROTECT)
    submitter = models.ForeignKey(
        User, related_name='submissions', on_delete=models.PROTECT)
    time_submitted = models.DateTimeField()
    zipfile = models.FileField(upload_to=submission_upload_to, blank=True)
    grade = models.FloatField(default=0.0)
    letter_grade = models.CharField(blank=True, max_length=16)
    comments = models.TextField(blank=True)
    under_review = models.BooleanField(default=False)

    def get_grade(self):
        return self.letter_grade or self.grade

    def save(self, *args, **kwargs):
        self.time_submitted = timezone.now()
        super(Submission, self).save(*args, **kwargs)

    def __str__(self):
        return u'%s: %s' % (self.assignment, self.submitter)


class PeerReviewSession(models.Model):
    assignment = models.OneToOneField(
        'Assignment', related_name='peer_review_session',
        on_delete=models.PROTECT)
    form_url = models.URLField()
    active = models.BooleanField(default=False)

    @transaction.atomic
    def new_review_or_none(self, submission, reviewer):
        # check if this person has already reviewed this submission
        # and if so return None
        try:
            review, new = self.reviews.get_or_create(
                submission=submission, reviewer=reviewer)
            if new:
                review.state = PeerReview.IN_PROGRESS
                review.save()
                submission.under_review = True
                submission.save()
                return review
            else:
                return None
        except PeerReview.MultipleObjectsReturned:
            return None

    def get_url(self):
        return (reverse(
            'course_review_assignment_view',
            kwargs={'assignment_id': self.assignment.id}))

    def __str__(self):
        return u'Peer review of %s' % self.assignment


class PeerReview(models.Model):
    # states
    NEW = 0
    IN_PROGRESS = 1
    COMPLETE = 2
    # grades
    NONE = -1
    HIGH_PASS = 0
    PASS = 1
    LOW_PASS = 2
    A_PLUS = 3
    A = 4
    A_MINUS = 5
    B_PLUS = 6
    B = 7
    B_MINUS = 8
    C_PLUS = 9
    C = 10
    C_MINUS = 11
    D_PLUS = 12
    D = 13
    F = 14
    STATE_CHOICES = [
        (NEW, 'New'),
        (IN_PROGRESS, 'In progress'),
        (COMPLETE, 'Complete'),
    ]
    GRADE_CHOICES = [
        (NONE, 'None'),
        (HIGH_PASS, 'H'),
        (PASS, 'P'),
        (LOW_PASS, 'L'),
        (A_PLUS, 'A+'),
        (A, 'A'),
        (A_MINUS, 'A-'),
        (B_PLUS, 'B+'),
        (B, 'B'),
        (B_MINUS, 'B-'),
        (C_PLUS, 'C+'),
        (C, 'C'),
        (C_MINUS, 'C-'),
        (D_PLUS, 'D+'),
        (D, 'D'),
        (F, 'F'),
    ]
    session = models.ForeignKey(
        'PeerReviewSession', related_name='reviews', on_delete=models.PROTECT)
    submission = models.ForeignKey(
        'Submission', related_name='reviews', on_delete=models.PROTECT)
    reviewer = models.ForeignKey(
        User, related_name='reviews', on_delete=models.PROTECT)
    state = models.PositiveSmallIntegerField(
        choices=STATE_CHOICES, default=NEW)
    suggested_grade = models.SmallIntegerField(
        choices=GRADE_CHOICES, default=NONE)

    def get_download_url(self):
        return (reverse(
            'course_download_reviewed_submission_view',
            kwargs={'review_id': self.id}))

    def get_submit_url(self):
        return (reverse(
            'course_submit_review_view',
            kwargs={'review_id': self.id}))

    @transaction.atomic
    def submit(self):
        if self.state == self.IN_PROGRESS:
            self.state = self.COMPLETE
            self.save()
            self.submission.under_review = False
            self.submission.save()

    def __str__(self):
        return "%s's review of %s" % (self.reviewer, self.submission)


PROXY = 'http://libproxy.lib.unc.edu/login?url='


class Linky:
    def __init__(self, stored_url, access_via_proxy, ignore_citation_url):
        self.url = ''
        self.stored_url = stored_url
        self.access_via_proxy = access_via_proxy
        self.ignore_citation_url = ignore_citation_url

    def linkify(self, html):
        html = re.sub(r' (https?://.+)\.', self.repl, html, 1)
        if self.stored_url and not self.url == self.stored_url:
            if self.access_via_proxy:
                anchor = self.stored_url[len(PROXY):]
            elif self.stored_url.startswith('/'):
                anchor = self.stored_url.split('.')[-1].upper()
            else:
                anchor = self.stored_url
            html = re.sub(
                r'</div>\n</div>',
                r' <a target="_blank" href="%s">%s</a>.</div>\n</div>' % (
                    self.stored_url, anchor), html, 1)
        return mark_safe(html)

    def repl(self, match):
        if self.ignore_citation_url:
            return ''
        self.url = match.group(1)
        if self.access_via_proxy:
            self.url = PROXY + self.url
        return (' <a target="_blank" href="%s">%s</a>.'
                % (self.url, match.group(1)))


class Reading(models.Model):
    zotero_id = models.CharField(max_length=16)
    citation_text = models.CharField(
        max_length=128, blank=True, editable=False)
    citation_html = models.TextField(blank=True, editable=False)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='courses/readings', blank=True)
    url = models.URLField(blank=True)
    access_via_proxy = models.BooleanField(default=False)
    access_via_ereserves = models.BooleanField(default=False)
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
        return ''

    def as_html(self):
        linky = Linky(
            self.get_url(), self.access_via_proxy, self.ignore_citation_url)
        unstyled_html = re.sub(r'style="[^"]+"', '', self.citation_html)
        return linky.linkify(unstyled_html)

    def word_count(self):
        if not self.centiwords:
            return None
        return '{:,}'.format(self.centiwords * 100)

    def __str__(self):
        return truncate(self.citation_text)

    class Meta:
        ordering = ('citation_text',)


class ReadingAssignment(models.Model):
    meeting = models.ForeignKey(
        'Meeting', related_name='reading_assignments',
        on_delete=models.CASCADE)
    reading = models.ForeignKey('Reading', on_delete=models.PROTECT)
    order = models.IntegerField(blank=True, null=True)
    discussion_leader = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True)
    discussion_questions = models.TextField(blank=True)
    is_optional = models.BooleanField(default=False)

    def discussion_questions_posted(self):
        return len(self.discussion_questions.strip()) > 0

    def get_absolute_url(self):
        return reverse('course_discussion_view', kwargs={
            'discussion_id': self.id})

    class Meta:
        ordering = ('order',)
