import re

from django.db import transaction
from django.contrib.auth.models import User
from django.core.management.base import CommandError

from courses.management.commands.utils import MyBaseCommand
from courses.models import Assignment, Submission


def grade_submission(course, username, assignment_slug, grade):
    print(username, assignment_slug, grade)
    user = User.objects.get(username=username)
    assignment = Assignment.objects.get(course=course, slug=assignment_slug)
    submission, created = Submission.objects.get_or_create(
        assignment=assignment, submitter=user)
    submission.grade = grade
    submission.save()
    return created


def comment_on_submission(course, username, assignment_slug, comments):
    print(username, assignment_slug, '%s comments' % len(comments))
    user = User.objects.get(username=username)
    assignment = Assignment.objects.get(course=course, slug=assignment_slug)
    submission, created = Submission.objects.get_or_create(
        assignment=assignment, submitter=user)
    submission.comments = ''.join(comments)
    submission.save()
    return created


class Command(MyBaseCommand):
    args = '<grade_and_comments_file.txt>'
    help = 'Grades submissions given a plain-text file of grades and comments.'

    @transaction.atomic
    def handle(self, *args, **options):
        if not len(args) == 1:
            raise CommandError(
                'Usage: grade_submissions <grade_and_comments_file.txt>')
        course = self.input_course()
        with open(args[0]) as f:
            username = assignment_slug = grade = None
            comments = []
            expecting = 'username'
            for l in f:
                if len(l.strip()) == 0:
                    if expecting == 'comment':
                        comments.append(l)
                    continue
                if expecting == 'username':
                    username = l.strip()
                    expecting = 'grade'
                elif expecting == 'grade':
                    m = re.match(r'^([-a-z]+):\s([.0-9]+)/[.0-9]+$', l.strip())
                    if m:
                        assignment_slug = m.group(1)
                        grade = float(m.group(2))
                        grade_submission(
                            course, username, assignment_slug, grade)
                    else:
                        comments.append(l)
                        expecting = 'comment'
                elif expecting == 'comment':
                    if re.match(r'^----+$', l.strip()):
                        comment_on_submission(
                            course, username, assignment_slug, comments)
                        comments = []
                        expecting = 'username'
                    else:
                        comments.append(l)
