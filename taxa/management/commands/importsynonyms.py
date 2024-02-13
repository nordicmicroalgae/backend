import csv
import os

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from taxa.models import Taxon, Synonym


DEFAULT_SYNONYMS_FILE = os.path.join(
    settings.CONTENT_DIR,
    'species',
    'synonyms.txt'
)

DEFAULT_SYNONYMS_FILE_ENCODING = 'utf8'



def transform_row(row):
    for field, value in row.items():
        if value.lower() in ['', 'na', 'n/a', 'null']:
            row[field] = None
    return row


class Command(BaseCommand):
    help = 'Import synonyms from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            default=DEFAULT_SYNONYMS_FILE,
            nargs='?',
            help=(
                'Path to CSV file containing synonyms. '
                'If this isn\'t provided, the path "%s" will be used.'
                % DEFAULT_SYNONYMS_FILE
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
            default=DEFAULT_SYNONYMS_FILE_ENCODING,
            help=(
                'Encoding used in CSV file containing synonyms. '
                'Default is "%s".' % DEFAULT_SYNONYMS_FILE_ENCODING
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
            '--author-field',
            default='author',
            help=(
                'Name of the field in the CSV file to use for '
                'authority. Default is "author".'
            ),
        )
        parser.add_argument(
            '--name-field',
            default='synonym_name',
            help=(
                'Name of the field in the CSV file to use for '
                'synonym name. Default is "synonym_name".'
            ),
        )


    def handle(self, *args, **options):
        filepath = options['file']
        encoding = options['encoding']
        clear_existing_objects = options['clear']
        id_field = options['id_field']
        author_field = options['author_field']
        name_field = options['name_field']
        verbosity = options['verbosity']

        objects_to_save = []

        # Part 1: Load rows from CSV file and convert to Django models.
        rows = []
        with open(filepath, 'r', encoding=encoding) as in_file:
            rows = list(map(
                transform_row,
                csv.DictReader(in_file, dialect='excel-tab')
            ))

        if len(rows) == 0:
            raise CommandError(
                'Found zero rows in specified CSV file. Aborting.'
            )

        for row in rows:
            object_args = {
                'taxon': row.get(id_field),
                'authority': row.get(author_field),
                'synonym_name': row.get(name_field),
            }

            # Resolve the taxon relationship.
            taxon_id = object_args.pop('taxon')
            try:
                object_args['taxon'] = (
                    Taxon.objects.get(pk=taxon_id)
                )
            except Taxon.DoesNotExist:
                if verbosity > 1:
                    self.stdout.write(self.style.WARNING(
                        'Taxon (%s) not found in database. '
                        'Skipping synonym name: %s.'
                        % (taxon_id, object_args['synonym_name'])
                    ))
                continue

            created_object = Synonym(**object_args)
            objects_to_save.append(created_object)


        # Part 2: Write the created models in one atomic operation.
        number_of_saved_objects = 0

        try:
            with transaction.atomic(savepoint=False):
                if clear_existing_objects:
                    Synonym.objects.all().delete()

                for object_to_save in objects_to_save:
                    object_to_save.save()
                    number_of_saved_objects = number_of_saved_objects + 1
        except Exception as e:
            raise CommandError(
                'Failed to write to database. '
                'Import aborted. Error was: %s' % e
            )

        if verbosity > 1:
            self.stdout.write(self.style.SUCCESS(
                'Successfully imported %u synonyms.'
                % number_of_saved_objects)
            )
