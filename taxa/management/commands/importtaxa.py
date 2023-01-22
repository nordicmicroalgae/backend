import csv
import itertools
import pathlib

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify

from taxa.models import Taxon


TAXA = pathlib.Path(settings.CONTENT_DIR, 'species', 'taxa_worms.txt')


class Command(BaseCommand):
    help = 'Import taxa from CSV file'

    def handle(self, *args, **options):
        number_of_existing_rows = Taxon.objects.all().count()

        # Clear existing taxa
        if number_of_existing_rows > 0:
            self.stdout.write('Clearing existing records from database...', ending='')
            Taxon.objects.all().delete()
            self.stdout.write(' done.')

        used_slugs = []

        def make_slug(scientific_name, authority):
            slug = slugify(scientific_name)

            if slug in used_slugs and authority:
                slug = '%s-%s' % (slug, slugify(authority))

            counter = itertools.count(1)
            while slug in used_slugs:
                slug = '%s-%d' % (slug, next(counter))

            used_slugs.append(slug)

            return slug


        def transform_row(row):
            for column, value in row.items():
                if value == '':
                    row[column] = None
            return row
            

        # Read CSV to dict
        with TAXA.open('r', encoding='cp1252') as in_file:
            rows = map(transform_row, csv.DictReader(in_file, dialect='excel-tab'))

            # Translate keys and store row dicts by id for easier lookup
            taxa_by_id = {
                row['aphia_id'] : {
                    'id': row['aphia_id'],
                    'parent_id': row['parent_id'],
                    'slug': make_slug(row['scientific_name'], row['authority']),
                    'scientific_name': row['scientific_name'],
                    'authority': row['authority'],
                    'rank': row['rank'],
                    'parent': {},
                    'classification': [],
                    'children': [],
                } for row in rows
            }

            # First iteration - Build up hierachial data for each taxon
            for taxon_info in taxa_by_id.values():
                parent_info = taxa_by_id.get(taxon_info['parent_id'], None)

                # Add parent and children
                if parent_info != None:
                    taxon_info['parent'] = {
                        'slug': parent_info['slug'],
                        'name': parent_info['scientific_name'],
                        'authority': parent_info['authority'],
                        'rank': parent_info['rank'],
                    }
                    parent_info['children'].append({
                        'slug': taxon_info['slug'],
                        'name': taxon_info['scientific_name'],
                        'authority': taxon_info['authority'],
                        'rank': taxon_info['rank'],
                    })

                # Add classification
                while parent_info != None:
                    taxon_info['classification'] = [{
                        'slug': parent_info['slug'],
                        'name': parent_info['scientific_name'],
                        'authority': parent_info['authority'],
                        'rank': parent_info['rank'],
                    }] + taxon_info['classification']

                    # Special insertae sedis cases, break the loop
                    if parent_info['parent_id'] == parent_info['id']:
                        self.stdout.write(self.style.WARNING(
                           'WARNING: Cannot build full classification. '
                           'Breaking out of infinite loop for: %s.' % ' -> '.join(
                               [c['name'] for c in taxon_info['classification']] +
                               [taxon_info['scientific_name']]
                           )
                        ))
                        break

                    # Move up to next parent
                    parent_info = taxa_by_id.get(parent_info['parent_id'], None)


            # Second iteration - Write each taxon to database
            for taxon_info in taxa_by_id.values():
                taxon = Taxon(**taxon_info)
                taxon.save()


            number_of_created_rows = Taxon.objects.all().count()

            self.stdout.write(self.style.SUCCESS(
                'Successfully imported %d taxa.' % number_of_created_rows
            ))
