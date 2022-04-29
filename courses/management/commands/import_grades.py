import csv

from django.db import transaction
from django.contrib.auth.models import User
from django.core.management.base import CommandError

from courses.management.commands.utils import MyBaseCommand
from courses.models import Submission


def get(row, column):
    try:
        return row[column]
    except:
        return row[column.capitalize()]


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
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    submitter = User.objects.get(username=get(row, 'username'))
                    submission, created = Submission.objects.get_or_create(
                        assignment=assignment,
                        submitter=submitter,
                    )
                    if str.isdigit(row['grade'].replace('.', '')):
                        submission.grade = float(get(row, 'grade'))
                        submission.letter_grade = ''
                    else:
                        submission.grade = 0.0
                        submission.letter_grade = get(row, 'grade')
                    try:
                        submission.comments = get(row, 'comment')
                    except:
                        submission.comments = ''
                    submission.save()
                except User.DoesNotExist:  # pylint: disable=E1101
                    raise CommandError('Cannot find user: %s ' % row['username'])
