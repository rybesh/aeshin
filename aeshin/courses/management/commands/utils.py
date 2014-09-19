from django.core.management.base import BaseCommand
from courses.models import Course
from datetime import date

class MyBaseCommand(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(MyBaseCommand, self).__init__(*args, **kwargs)
    
    def input_ok(self, prompt='OK'):
        if not prompt.endswith('OK'):
            prompt += ', OK'
        answer = raw_input('%s? [y/N]:' % prompt)
        return (answer.lower() == 'y')

    def input_course(self, include_archived=False):
        if include_archived:
            courses = Course.objects.all()
        else:
            courses = Course.objects.filter(is_archived=False)
        for course in courses:
            self.stdout.write('(%s) %s\n' % (course.id, course))
        while True:
            course_id = raw_input('Course ID: ')
            try:
                return Course.objects.get(id=course_id)
            except (ValueError, Course.DoesNotExist):
                self.stdout.write('Please choose one of the course IDs listed above.\n')

    def input_assignment(self, course):
        assignments = course.assignment_set.all()
        for assignment in assignments:
            self.stdout.write('(%s) %s\n' % (assignment.id, assignment))
        while True:
            assignment_id = raw_input('Assignment ID: ')
            try:
                return Assignment.objects.get(id=assignment_id)
            except (ValueError, Assignment.DoesNotExist):
                self.stdout.write('Please choose one of the assignment IDs listed above.\n')

    def input_date(self, prompt='YYYY-MM-DD'):
        while True:
            try:
                datestring = raw_input('%s: ' % prompt)
                return date(*[int(x) for x in datestring.split('-')])
            except:
                self.stdout.write('Please enter a date using the format YYYY-MM-DD.\n')

    def input_choices_index(self, choices):
        for i, choice in enumerate(choices):
            self.stdout.write('(%s) %s\n' % (i+1, choice))
        while True:
            try:
                return (int(raw_input('Choice: ')) - 1)
            except (IndexError, TypeError):
                self.stdout.write('Please choose one of the numbers listed above.\n')

    def input_choices(self, choices):
        return choices[self.input_choices_index(choices)]

    
            
