import csv

from django.db import transaction
from django.contrib.auth.models import User
from django.core.management.base import CommandError

from courses.management.commands.utils import MyBaseCommand
from courses.models import Submission


class Command(MyBaseCommand):
    args = '<grades.csv>'
    help = 'a CSV file of grades.'

    def add_arguments(self, parser):
        parser.add_argument('grades')

    @transaction.atomic
    def handle(self, *args, **options):

        course = self.input_course()
        assignment = self.input_assignment(course)

        with open(options['grades'], newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # skip header
            for row in csv.reader(csvfile):
                username, grade, comments = row[:3]
                try:
                    submitter = User.objects.get(username=username)
                    submission, created = Submission.objects.get_or_create(
                        assignment=assignment,
                        submitter=submitter,
                    )
                    if str.isdigit(grade.replace('.', '')):
                        submission.grade = float(grade)
                        submission.letter_grade = ''
                    else:
                        submission.grade = 0.0
                        submission.letter_grade = grade
                    submission.comments = comments
                    submission.save()
                except User.DoesNotExist:  # pylint: disable=E1101
                    raise CommandError('Cannot find user: %s ' % username)
