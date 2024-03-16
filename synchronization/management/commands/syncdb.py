import tempfile

from django.db import transaction
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Synchronize database with content repo'

    def write(self, *args, **kwargs):
        if self.verbosity > 0:
            self.stdout.write(*args, **kwargs)

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']

        media_file = tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf8',
        )

        self.write('Starting synchronization job.\n\n')
        self.write('This will probably take some time.')
        self.write('Go grab a cup of coffee! ☕️\n\n')

        with transaction.atomic(savepoint=False):
            # pre-import jobs
            self.write('Step 1/5: Exporting media')
            call_command('exportmedia', output=media_file.name, **options)
            self.write('')

            # import jobs
            self.write('Step 2/5: Importing taxa')
            call_command('importtaxa', clear=True, **options)
            self.write('')

            self.write('Step 3/5: Importing synonyms')
            call_command('importsynonyms', clear=True, **options)
            self.write('')

            self.write('Step 4/5: Importing facts')
            call_command('importfacts', **options)
            self.write('')

            # post-import jobs
            self.write('Step 5/5: Importing media')
            call_command('importmedia', media_file.name, clear=True, **options)
            self.write('')

        self.write('Synchronization job completed.')
