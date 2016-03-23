import re

from django.db import transaction
from django.contrib.auth.models import User
from django.core.management.base import CommandError

from courses.management.commands.utils import MyBaseCommand
from courses.models import Assignment, Submission


def grade_submission(course, username, assignment_slug, grade):
    user = User.objects.get(username=username)
    assignment = Assignment.objects.get(course=course, slug=assignment_slug)
    submission = Submission.objects.get(assignment=assignment, submitter=user)
    submission.grade = grade
    submission.save()


def comment_on_submission(course, username, assignment_slug, comments):
    user = User.objects.get(username=username)
    assignment = Assignment.objects.get(course=course, slug=assignment_slug)
    submission = Submission.objects.get(assignment=assignment, submitter=user)
    submission.comments = comments.join('\n')
    submission.save()


class Command(MyBaseCommand):
    args = '<grade_and_comments_file.txt>'
    help = 'Grades submissions given a plain-text file of grades and comments.'

    @transaction.atomic
    def handle(self, *args, **options):
        if not len(args) == 1:
            raise CommandError(
                'Usage: grade_submissions <grade_and_comments_file.txt>')
        course = self.input_course()
        with open(args[1]) as f:
            username = assignment_slug = grade = None
            comments = []
            expecting = 'username'
            for line in f:
                l = line.strip()
                if len(line) == 0:
                    continue
                if expecting == 'username':
                    username = l
                    expecting = 'grade'
                elif expecting == 'grade':
                    m = re.match(r'^([-a-z]+):\s([0-9]+)/[0-9]+$', l)
                    assignment_slug = m.group(1)
                    grade = float(m.group(2))
                    grade_submission(course, username, assignment_slug, grade)
                elif expecting == 'comment':
                    if re.match(r'^----+$', l):
                        comment_on_submission(
                            course, username, assignment_slug, comments)
                    else:
                        comments.append(l)
