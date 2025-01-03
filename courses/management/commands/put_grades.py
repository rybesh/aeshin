import csv
from django.db import transaction
from django.contrib.auth.models import User
from django.core.management.base import CommandError
from courses.management.commands.utils import MyBaseCommand
from courses.models import Assignment, Submission


class Command(MyBaseCommand):
    args = "<grades.csv>"
    help = "a CSV file of semester grades"

    def add_arguments(self, parser):
        parser.add_argument("grades")

    @transaction.atomic
    def handle(self, *_, **options):
        course = self.input_course()

        with open(options["grades"], newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            assert reader.fieldnames is not None
            assignment_ids = set(
                [f.split(" | ")[1] for f in reader.fieldnames[2:] if " | " in f]
            )
            for row in reader:
                try:
                    submitter = User.objects.get(username=row["Username"])
                    counts = {"created": 0, "updated": 0}
                    for assignment_id in assignment_ids:

                        assignment = Assignment.objects.get(id=assignment_id)
                        assert assignment.course.id == course.id

                        submission, created = Submission.objects.get_or_create(
                            assignment=assignment,
                            submitter=submitter,
                        )
                        if created:
                            counts["created"] += 1
                        else:
                            counts["updated"] += 1

                        prefix = f"{assignment.title} | {assignment.id} | "
                        grade = row[f"{prefix}Grade"]
                        comment = row[f"{prefix}Comment"]

                        if assignment.is_letter_graded:
                            submission.grade = 0.0
                            submission.letter_grade = grade
                        else:
                            submission.grade = 0.0 if grade == "" else float(grade)
                            submission.letter_grade = ""

                        submission.comments = comment
                        submission.save()

                    self.stderr.write(
                        f"{submitter.get_full_name()}: updated {counts['updated']} assignments and created {counts['created']} new ones."
                    )

                except User.DoesNotExist:
                    raise CommandError(f"Cannot find user: {row['Username']}")
                except Assignment.DoesNotExist as e:
                    raise CommandError(f"Cannot find assignment: {e}")
