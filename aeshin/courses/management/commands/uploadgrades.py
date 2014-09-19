import itertools
import gdata.spreadsheet.service
import getpass

from django.db import transaction
from django.contrib.auth.models import User
from django.core.management.base import CommandError

from courses.management.commands.utils import MyBaseCommand
from courses.models import Submission

def row_to_data(header, row):
    return { 'email': row[header.index('Your email address')],
             'grade': row[header.index('Total grade')],
             'comments': '\n\n'.join(row) }

def create_submission(assignment, data):
    try:
        submitter = User.objects.get(email=data['email'])
        submission = Submission(
            assignment=assignment,
            submitter=submitter,
            grade=data['grade'],
            comments=data['comments'])
        submission.save()
    except Submission.DoesNotExist: # pylint: disable=E1101
        raise CommandError('Cannot find %s ' % data['email'])

def sheets_connect():
    client = gdata.spreadsheet.service.SpreadsheetsService()
    client.email = raw_input('Email: ')
    client.password = getpass.getpass('Password: ')
    client.source = 'org.aeshin.uploadgrades.py'
    client.ProgrammaticLogin()
    return client
    
def get_sheet_rows(client, sheet):
    ss_key = sheet.id.text.split('/')[-1]
    ws_feed = client.GetWorksheetsFeed(ss_key)
    ws_key = ws_feed.entry[0].id.text.split('/')[-1]
    cells_feed = client.GetCellsFeed(ss_key, ws_key)
    rows = [ [ c.content.text for c in cells ] for _, cells
             in itertools.groupby(cells_feed.entry, lambda e: e.cell.row) ]
    return rows
    
class Command(MyBaseCommand):
    help = 'Uploads grades from a Google spreadsheet.'

    @transaction.atomic
    def handle(self, *args, **options):
        client = sheets_connect()
        ss_feed = client.GetSpreadsheetsFeed()
        sheets = [e for e in ss_feed.entry if e.title.text.startswith("Probe")]
        sheet_names = [ s.title.text for s in sheets ]
        sheet = sheets[self.input_choices_index(sheet_names)]
        rows = get_sheet_rows(client, sheet)
        course = self.input_course()
        assignment = self.input_assignment(course)

        for row in rows[1:]:
            create_submission(assignment, row_to_data(rows[0], row))

        self.stdout.write('%s submissions added' % len(rows[1:]))
