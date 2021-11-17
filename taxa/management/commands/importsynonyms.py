import csv
import json
import pathlib

from django.core.management.base import BaseCommand
from django.conf import settings

from taxa.models import Synonym, Taxon
from taxa.utils import transform_keys


SYNONYMS_ALGAEBASE = pathlib.Path(
    settings.CONTENT_DIR,
    'species', 'synonyms_algaebase.txt'
)
SYNONYMS_DYNTAXA = pathlib.Path(
    settings.CONTENT_DIR,
    'species', 'synonyms_dyntaxa.txt'
)


class Command(BaseCommand):
    help = 'Import synonyms from CSV files'

    def handle(self, *args, **options):
        number_of_existing_rows = Synonym.objects.all().count()

        # Clear existing synonyms
        if number_of_existing_rows > 0:
            self.stdout.write('Clearing existing records from database...', ending='')
            Synonym.objects.all().delete()
            self.stdout.write(' done.')

        rows = []

        # Read CSV to list of dicts
        with SYNONYMS_ALGAEBASE.open('r', encoding='utf16') as in_file:
            rows = rows + list(csv.DictReader(in_file, dialect='excel-tab'))

        with SYNONYMS_DYNTAXA.open('r', encoding='utf16') as in_file:
            rows = rows + list(csv.DictReader(in_file, dialect='excel-tab'))


        for row in rows:
            # Integrity check
            try:
                taxon = Taxon.objects.get(pk=row['Scientific name'])
            except Taxon.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                   'WARNING: Current name: "%s" not found in database. '
                   'Skipping synonym name: "%s."'
                   % (row['Scientific name'], row['Synonym name'])
                ))
                continue

            # Write synonym to database
            synonym = Synonym(
               scientific_name=row['Synonym name'],
               authority=row['Synonym author'],
               additional_info=json.loads(
                   row.get('Info json', '{}'),
                   object_hook=transform_keys
                ),
            )
            synonym.current_name = taxon
            synonym.save()


        number_of_created_rows = Synonym.objects.all().count()

        self.stdout.write(self.style.SUCCESS(
            'Successfully imported %d synonyms.' % number_of_created_rows
        ))
