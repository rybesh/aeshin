from datetime import timedelta
from django.core.management.base import CommandError
from django.db import transaction
from courses.models import Meeting, ReadingAssignment, ViewingAssignment
from courses.management.commands.utils import MyBaseCommand


def push_from_weekend(date, days):
    if date.weekday() > 3:  # Friday or weekend
        if days == "MW":
            nextday = 7
        else:  # TTH
            nextday = 8
        return date + timedelta(days=(nextday - date.weekday()))
    return date


class Command(MyBaseCommand):
    help = "Copies all meetings from an old course to a new course."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Choose the old course:\n")
        old_course = self.input_course(include_archived=True)
        old_meetings = old_course.meetings.all()
        self.stdout.write("Choose the new course:\n")
        new_course = self.input_course()
        start_date = self.input_date("Start date of new course")
        delta = start_date - old_meetings[0].date
        self.stdout.write("What days does the new course meet?\n")
        days = self.input_choices(["MW", "TTH"])
        previous_meeting = None
        for old_meeting in old_meetings:
            new_meeting = Meeting()
            new_meeting.course = new_course
            new_meeting.date = push_from_weekend(old_meeting.date + delta, days)
            if previous_meeting and new_meeting.date == previous_meeting.date:
                new_meeting.date = push_from_weekend(
                    new_meeting.date + timedelta(days=2), days
                )
            new_meeting.title = old_meeting.title
            new_meeting.description = old_meeting.description
            new_meeting.save()
            for ra in ReadingAssignment.objects.filter(meeting=old_meeting):
                ra.pk = None  # create a new ReadingAssignment with same props
                ra.meeting = new_meeting
                ra.save()
            for va in ViewingAssignment.objects.filter(meeting=old_meeting):
                va.pk = None  # create a new ViewingAssignment with same props
                va.meeting = new_meeting
                va.save()
            self.stdout.write("%s\n" % new_meeting)
            previous_meeting = new_meeting
        if not self.input_ok("Keep these changes"):
            raise CommandError("Course was not copied.")
