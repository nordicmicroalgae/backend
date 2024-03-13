import csv
from collections import defaultdict

from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


from facts.models import Facts


class Command(BaseCommand):
    help = 'Import external links from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            help=(
                'Path to CSV file containing external links.'
            ),
        )
        parser.add_argument(
            '-e',
            '--encoding',
            default='utf8',
            help=(
                'Encoding used in CSV file. Default is "utf8".'
            ),
        )
        parser.add_argument(
            '--provider',
            help=(
                'Provider of the external links. '
                'For example: AlgaeBase'
            ),
            required=True,
        )
        parser.add_argument(
            '--collection',
            default='External Links',
            help=(
                'Facts collection name. Default is "External Links".'
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
            '--external-id-field',
            default='external_taxon_id',
            help=(
                'Name of the field in the CSV file to use as external '
                'taxon identifier. Default is "external_taxon_id".'
            ),
        )
        parser.add_argument(
            '--note-field',
            help=(
                'Name of a field in the CSV file to '
                'use as a note for the external link.'
            ),
        )
        parser.add_argument(
            '--url-template',
            help=(
                'Template for which an external URL is generated '
                'from. <replace_id> is replaced by the value from '
                'the external id field. This could also be a '
                'reference to a field in the CSV file to use either '
                'as-is or as template on a row basis.'
            ),
            required=True,
        )


    def handle(self, *args, **options):
        filepath = options['file']
        encoding = options['encoding']
        provider = options['provider']
        collection = options['collection']
        id_field = options['id_field']
        external_id_field = options['external_id_field']
        note_field = options['note_field']
        url_template = options['url_template']
        verbosity = options['verbosity']

        objects_to_save = []

        required_fields = dict(
            id_field=id_field,
            external_id_field=external_id_field,
        )

        if note_field:
            required_fields['note_field'] = note_field

        links_by_taxon_id = defaultdict(list)

        # Part 1: Load rows from CSV file into dicts.
        cols, rows = [], []
        with open(filepath, 'r', encoding=encoding) as in_file:
            reader = csv.DictReader(in_file, dialect='excel-tab')
            cols = reader.fieldnames
            rows = list(reader)

        if len(rows) == 0:
            raise CommandError(
                'Found zero rows in specified CSV file. Aborting.'
            )

        for field_arg, field_name in required_fields.items():
            if field_name not in cols:
                raise CommandError(
                    'Field %s does not exist in found headers. '
                    'Please provide another value for %s. '
                    'Possible values are: %s.'
                    % (field_name, field_arg, ', '.join(cols))
                )

        for row in rows:
            taxon_id = row[id_field].strip()
            external_id = row[external_id_field].strip()

            if taxon_id == '':
                if verbosity > 1:
                    self.stdout.write(self.style.WARNING(
                        '%s must not be empty. Skipping row.' % id_field
                    ))
                continue

            if external_id == '':
                if verbosity > 1:
                    self.stdout.write(self.style.WARNING(
                        '%s must not be empty. Skipping row.'
                        % external_id_field
                    ))
                continue

            row_url_template = row.get(url_template, url_template)

            if row_url_template == '':
                if verbosity > 1:
                    self.stdout.write(self.style.WARNING(
                        'url_template must not be empty. Skipping row.'
                    ))
                continue

            if not row_url_template.startswith('http'):
                row_url_template = 'https://{}'.format(row_url_template)

            link_dict = {
                'external_id': external_id,
                'external_url': (
                    row_url_template.replace(
                        '<replace_id>',
                        external_id
                    )
                ),
            }

            if note_field:
                link_dict['note'] = row[note_field].strip()

            links_by_taxon_id[taxon_id].append(link_dict)


        # Part 2: Create or update Django models from dicts.
        for taxon_id, external_links in links_by_taxon_id.items():
            facts_dict = {
                'collection': collection,
                'provider': provider,
                'attributes': external_links,
            }

            try:
                facts = Facts.objects.get(pk=taxon_id)
            except Facts.DoesNotExist:
                facts = Facts(pk=taxon_id)

            facts.add_or_replace(facts_dict)

            objects_to_save.append(facts)


        # Part 3: Write created or updated models in one atomic operation.
        number_of_saved_objects = 0
        try:
            with transaction.atomic(savepoint=False):
                for object_to_save in objects_to_save:
                    try:
                        object_to_save.full_clean()
                    except ValidationError as e:
                        validation_messages = ', '.join([
                            '%s: %s' % (field, ', '.join(errors))
                            for field, errors in e.message_dict.items()
                        ])
                        if verbosity > 1:
                            self.stdout.write(self.style.WARNING(
                                'Skipping invalid %s links. Error(s) was: %s'
                                % (provider, validation_messages)
                            ))
                        continue

                    object_to_save.save()
                    number_of_saved_objects = number_of_saved_objects + 1
        except Exception as e:
            raise CommandError(
                'Failed to write to database. '
                'Import aborted. Error was %s.' % e
            )

        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS(
                'Succesfully imported %s external links for %u taxa.'
                % (provider, number_of_saved_objects)
            ))
