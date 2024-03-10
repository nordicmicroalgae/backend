import csv
import itertools
import os

from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.text import slugify

from taxa.models import Taxon


DEFAULT_TAXA_FILE = os.path.join(
    settings.CONTENT_DIR,
    'species',
    'taxa.txt'
)

DEFAULT_TAXA_FILE_ENCODING = 'utf8'


class SlugGenerator:

    def __init__(self, used_slugs = []):
        self.used_slugs = used_slugs
        self.slug_base = None
        self.counter_by_base = {}

    def __call__(self, scientific_name, authority):
        self.slug_base = (scientific_name, authority)
        return self

    def __next__(self):
        scientific_name, authority = self.slug_base

        slug = slugify(scientific_name)

        if slug in self.used_slugs and authority:
            slug = '%s-%s' % (slug, slugify(authority))

        while slug in self.used_slugs:
            slug = '%s-%d' % (slug, next(self.counter))

        self.used_slugs.append(slug)

        return slug

    @property
    def counter(self):
        if not self.slug_base in self.counter_by_base:
            self.counter_by_base[self.slug_base] = itertools.count(1)
        return self.counter_by_base[self.slug_base]


def get_used_slugs():
    queryset = Taxon.objects.all()
    return list(queryset.values_list('slug', flat=True))


def transform_row(row):
    for field, value in row.items():
        if value.lower() in ['', 'na', 'n/a', 'null']:
            row[field] = None
    return row


class Command(BaseCommand):
    help = 'Import taxa from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            default=DEFAULT_TAXA_FILE,
            nargs='?',
            help=(
                'Path to CSV file containing taxa. '
                'If this isn\'t provided, the path "%s" will be used.'
                % DEFAULT_TAXA_FILE
            ),
        )
        parser.add_argument(
            '-c',
            '--clear',
            action='store_true',
            help=(
                'Clear any existing objects from '
                'database before writing new ones.'
            ),
        )
        parser.add_argument(
            '-e',
            '--encoding',
            default=DEFAULT_TAXA_FILE_ENCODING,
            help=(
                'Encoding used in CSV file containing taxa. '
                'Default is "%s".' % DEFAULT_TAXA_FILE_ENCODING
            ),
        )
        parser.add_argument(
            '--id-field',
            default='taxon_id',
            help=(
                'Name of the field in the CSV file to use as '
                'taxon identifier. Default is "taxon_id".'
            ),
        )
        parser.add_argument(
            '--parent-id-field',
            default='parent_id',
            help=(
                'Name of the field in the CSV file to use as '
                'parent taxon identifier. Default is "parent_id".'
            ),
        )

    def handle(self, *args, **options):
        filepath = options['file']
        encoding = options['encoding']
        clear_existing_objects = options['clear']
        id_field = options['id_field']
        parent_id_field = options['parent_id_field']
        verbosity = options['verbosity']

        taxa_by_id = {}

        if clear_existing_objects:
            preexisting_slugs = []
        else:
            preexisting_slugs = get_used_slugs()

        slugs = SlugGenerator(used_slugs=preexisting_slugs)

        # Part 1: Load rows from CSV file into dicts.
        with open(filepath, 'r', encoding=encoding) as in_file:
            rows = map(transform_row, csv.DictReader(in_file, dialect='excel-tab'))

            # Translate keys and store row dicts by id for easier lookup
            taxa_by_id = {
                row[id_field] : {
                    'id': row[id_field],
                    'parent_id': row[parent_id_field],
                    'slug': next(slugs(row['scientific_name'], row['authority'])),
                    'scientific_name': row['scientific_name'],
                    'authority': row['authority'],
                    'rank': row['rank'],
                    'parent': {},
                    'classification': [],
                    'children': [],
                } for row in rows
            }

            # Build up hierachial data for each taxon
            for taxon_info in taxa_by_id.values():
                parent_info = taxa_by_id.get(taxon_info['parent_id'])

                # Add parent and children
                if parent_info != None:
                    taxon_info['parent'] = {
                        'slug': parent_info['slug'],
                        'scientific_name': parent_info['scientific_name'],
                        'authority': parent_info['authority'],
                        'rank': parent_info['rank'],
                    }
                    parent_info['children'].append({
                        'slug': taxon_info['slug'],
                        'scientific_name': taxon_info['scientific_name'],
                        'authority': taxon_info['authority'],
                        'rank': taxon_info['rank'],
                    })

                # Add classification
                while parent_info != None:
                    taxon_info['classification'] = [{
                        'slug': parent_info['slug'],
                        'scientific_name': parent_info['scientific_name'],
                        'authority': parent_info['authority'],
                        'rank': parent_info['rank'],
                    }] + taxon_info['classification']

                    # Special insertae sedis cases, break the loop
                    if parent_info['parent_id'] == parent_info['id']:
                        if verbosity > 1:
                            incomplete_classification = list(map(
                                lambda t: t['scientific_name'],
                                taxon_info['classification'] + [taxon_info]
                            ))
                            self.stdout.write(self.style.WARNING(
                                'Cannot build full classification. '
                                'Breaking out of infinite loop for: %s.'
                                % ' -> '.join(incomplete_classification)
                            ))

                        break

                    # Move up to next parent
                    parent_info = taxa_by_id.get(parent_info['parent_id'])


        # Part 2: Create models and write in one atomic operation.
        number_of_saved_objects = 0

        try:
            with transaction.atomic(savepoint=False):
                if clear_existing_objects:
                    Taxon.objects.all().delete()

                for taxon_info in taxa_by_id.values():
                    taxon = Taxon(**taxon_info)

                    try:
                        taxon.full_clean(
                            # safe-to-exclude components built for convenience
                            exclude=['classification', 'children', 'parent']
                        )
                    except ValidationError as e:
                        validation_messages = ', '.join([
                            '%s: %s' % (field, ', '.join(errors))
                            for field, errors in e.message_dict.items()
                        ])
                        if verbosity > 1:
                            self.stdout.write(self.style.WARNING(
                                'Skipping invalid taxon %s (%u). Error(s) was: %s' % (
                                    taxon.scientific_name or 'unkown',
                                    taxon.id or 'unkown',
                                    validation_messages
                                )
                            ))
                        continue

                    taxon.save(force_insert=True)
                    number_of_saved_objects = number_of_saved_objects + 1
        except Exception as e:
            raise CommandError(
                'Failed to write to database. '
                'Import aborted. Error was: %s' % e
            )

        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS(
                'Successfully imported %u taxa.'
                % number_of_saved_objects
            ))
