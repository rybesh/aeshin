from django.contrib.auth.models import User
from django.core.management.base import CommandError
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.crypto import get_random_string
from courses.management.commands.utils import MyBaseCommand
import csv


class Command(MyBaseCommand):
    help = "Creates student accounts and adds them to a course."

    def add_arguments(self, parser):
        parser.add_argument("roster")

    @transaction.atomic
    def handle(self, *_, **options):
        roster = options["roster"]
        reader = csv.DictReader
        students = []
        new_count = existing_count = 0
        for row in reader(open(roster, "rt", encoding="utf8")):
            try:
                last_name, first_name = [x.strip() for x in row["Name"].split(",")]
                email = row["Email"].strip()
                username = email.split("@")[0]
                try:
                    student, created = User.objects.get_or_create(
                        first_name=first_name,
                        last_name=last_name,
                        defaults={"username": username},
                    )
                    if created:
                        self.stdout.write(
                            "New student: %s %s (%s)\n" % (first_name, last_name, email)
                        )
                        student.set_password(get_random_string(32))
                        new_count += 1
                    else:
                        self.stdout.write(
                            "Old student: %s %s (%s)\n" % (first_name, last_name, email)
                        )
                        existing_count += 1
                    student.email = email
                    student.is_active = True
                    student.save()
                    students.append(student)
                except IntegrityError:
                    raise CommandError("Username collision: %s" % username)
            except KeyError as e:
                raise CommandError("%s is missing a %s value." % (roster, e))
        self.stdout.write(
            "%s new students and %s existing students.\n" % (new_count, existing_count)
        )
        self.stdout.write("To which course will these students be added?\n")
        course = self.input_course()
        added_count = existing_count = 0
        for student in course.students.all():
            if student not in students:
                self.stdout.write(
                    "%s appears to have dropped the course.\n" % student.email
                )
        for student in students:
            if course.has_student(student):
                existing_count += 1
            else:
                course.students.add(student)
                self.stdout.write("%s\n" % student.email)
                added_count += 1
        self.stdout.write(
            "%s students added (%s already in that course).\n"
            % (added_count, existing_count)
        )
