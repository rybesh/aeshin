import csv

from django.db import transaction

from courses.management.commands.utils import MyBaseCommand
from courses.models import PeerReview

GRADES = dict(PeerReview.GRADE_CHOICES)


def summarize(submission, comments):
    reviews = submission.reviews.filter(
        reviewer__is_staff=True,
        state=PeerReview.COMPLETE
    )
    return {
        'name': '%s (%s %s)' % (
            submission.submitter.username,
            submission.submitter.first_name,
            submission.submitter.last_name,
        ),
        'reviewers': ' / '.join([r.reviewer.last_name for r in reviews]),
        'grade': ' / '.join([GRADES[r.suggested_grade] for r in reviews]),
        'comments': '\n\n'.join(
            [comments.get(r.id, ('MISSING', ''))[1] for r in reviews]
        ),
        'review_ids': ' / '.join(
            [comments.get(r.id, ('MISSING', ''))[0] for r in reviews]
        ),
    }


class Command(MyBaseCommand):
    args = '<reviews.csv>'
    help = 'Grades submissions given a CSV file of reviews.'

    def read_comments(self, filename):
        comment_index = None
        comments = {}
        with open(filename, newline='') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i == 0:
                    print('Please choose the comments field:')
                    comment_index = self.input_choices_index(row)
                else:
                    try:
                        comments[int(row[-1])] = (
                            str(i),
                            row[comment_index].strip(),
                        )
                    except ValueError:
                        pass
        return comments

    def add_arguments(self, parser):
        parser.add_argument('reviews')

    @transaction.atomic
    def handle(self, *args, **options):

        course = self.input_course()
        assignment = self.input_assignment(course)
        comments = self.read_comments(options['reviews'])

        with open('results.csv', 'w', newline='') as results:
            o = csv.writer(results)
            o.writerow([
                'Submission ID',
                'Name',
                'Reviewers',
                'Grades',
                'Comments',
                'Review IDs',
            ])

            for submission in assignment.submissions.all():
                summary = summarize(submission, comments)
                o.writerow([
                    submission.id,
                    summary['name'],
                    summary['reviewers'],
                    summary['grade'],
                    summary['comments'],
                    summary['review_ids'],
                ])
                submission.letter_grade = summary['grade']
                submission.comments = summary['comments']
                submission.save()
