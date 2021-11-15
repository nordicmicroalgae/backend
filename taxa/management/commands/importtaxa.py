import csv
import pathlib

from django.core.management.base import BaseCommand
from django.conf import settings

from taxa.models import Taxon


DYNTAXA = pathlib.Path(settings.CONTENT_DIR, 'species', 'taxa_dyntaxa.txt')


class Command(BaseCommand):
    help = 'Import taxa from CSV file'

    def handle(self, *args, **options):
        number_of_existing_rows = Taxon.objects.all().count()

        # Clear existing taxa
        if number_of_existing_rows > 0:
            self.stdout.write('Clearing existing records from database...', ending='')
            Taxon.objects.all().delete()
            self.stdout.write(' done.')

        # Read CSV to dict
        with DYNTAXA.open('r', encoding='utf16') as in_file:
            rows = csv.DictReader(in_file, dialect='excel-tab')

            # Translate keys and store row dicts by name for easier lookup
            taxa_by_name = {
               row['Scientific name']: {
                   'scientific_name': row['Scientific name'],
                   'parent_name': row['Parent name'],
                   'authority': row['Author'],
                   'rank': row['Rank'],
                   'classification': [],
                   'children': [],
               } for row in rows
            }

            # First iteration - Build up hierachial data for each taxon
            for taxon_info in taxa_by_name.values():
                parent_info = taxa_by_name.get(taxon_info['parent_name'], None)

                # Add children
                if parent_info != None:
                    parent_info['children'].append(taxon_info['scientific_name'])

                # Add classification
                while parent_info != None:
                    taxon_info['classification'] = [{
                        'name': parent_info['scientific_name'],
                        'rank': parent_info['rank'],
                    }] + taxon_info['classification']

                    # Special insertae sedis cases, break the loop
                    if parent_info['parent_name'] == parent_info['scientific_name']:
                        self.stdout.write(self.style.WARNING(
                           'WARNING: Cannot build full classification. '
                           'Breaking out of infinite loop for: %s.' % ' -> '.join(
                               [c['name'] for c in taxon_info['classification']] +
                               [taxon_info['scientific_name']]
                           )
                        ))
                        break

                    # Move up to next parent
                    parent_info = taxa_by_name.get(parent_info['parent_name'], None)


            # Second iteration - Write each taxon to database
            for taxon_info in taxa_by_name.values():
                taxon = Taxon(**taxon_info)
                taxon.save()


            number_of_created_rows = Taxon.objects.all().count()

            self.stdout.write(self.style.SUCCESS(
                'Successfully imported %d taxa.' % number_of_created_rows
            ))
