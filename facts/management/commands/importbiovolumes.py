import csv

from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from facts.models import Facts


GENERAL_FIELD_MAPPINGS = {
    'division': 'Division',
    'class': 'Class',
    'order': 'Order',
    'genus': 'Genus',
    'species': 'Species',
    'sflag': 'SFLAG',
    'authority': 'Author',
    'trophy': 'Trophy',
    'geometric_shape': 'Geometric_shape',
    'formula': 'FORMULA',
    'list': 'List',
}

SIZE_CLASS_FIELD_MAPPINGS = {
    'size_class_no': 'SizeClassNo',
    'unit': 'Unit',
    'size_range': 'SizeRange',
    'length1': 'Length(l1)µm',
    'length2': 'Length(l2)µm',
    'width': 'Width(w)µm',
    'height': 'Height(h)µm',
    'diameter1': 'Diameter(d1)µm',
    'diameter2': 'Diameter(d2)µm',
    'no_of_cells_per_counting_unit': 'No_of_cells/counting_unit',
    'calculated_volume': 'Calculated_volume_µm3',
    'comment': 'Comment',
    'filament_length_of_cell': 'Filament_length_of_cell(µm)',
    'calculated_carbon_pg_per_counting_unit': 'Calculated_Carbon_pg/counting_unit',
    'comment_on_carbon_calculation': 'Comment_on_Carbon_calculation',
    'stage': 'STAGE',
}


class Command(BaseCommand):
    help = 'Import biovolumes from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            help=(
                'Path to CSV file containing biovolumes.'
            ),
        )
        parser.add_argument(
            '-e',
            '--encoding',
            default='cp1252',
            help=(
                'Encoding used in CSV file. Default is "cp1252".'
            ),
        )
        parser.add_argument(
            '--provider',
            help=(
                'Provider of biovolumes data. For example: NOMP'
            ),
            required=True,
        )
        parser.add_argument(
            '--collection',
            default='Biovolumes',
            help=(
                'Facts collection name. Default is "Biovolumes".'
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

    def handle(self, *args, **options):
        filepath = options['file']
        encoding = options['encoding']
        provider = options['provider']
        collection = options['collection']
        id_field = options['id_field']
        verbosity = options['verbosity']

        objects_to_save = []

        biovolumes_by_taxon = {}

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

        if id_field not in cols:
            raise CommandError(
                'Field %s does not exist in found headers. '
                'Please provide another value for --id-field. '
                'Possible values are: %s.'
                % (id_field, ', '.join(cols))
            )

        missing_fields = list(filter(
            lambda required_field: required_field not in cols,
            list(GENERAL_FIELD_MAPPINGS.values()) +
            list(SIZE_CLASS_FIELD_MAPPINGS.values())
        ))

        if missing_fields:
            raise CommandError(
                'Required field(s) %s does not exist in found headers. '
                'Aborting.' % ', '.join(missing_fields)
            )

        for row_index, row in enumerate(rows):
            if None in row.values():
                self.stdout.write(self.style.WARNING(
                    'Seems like malformed row: %u. Skipping row.'
                    % (row_index + 2)
                ))
                continue

            taxon_id = row[id_field].strip()

            if taxon_id == '':
                if verbosity > 1:
                    self.stdout.write(self.style.WARNING(
                        '%s must not be empty. Skipping row.' % id_field
                    ))
                continue

            if taxon_id not in biovolumes_by_taxon:
                biovolumes_by_taxon[taxon_id] = {
                    'size_classes': [],
                }

                for key, column in GENERAL_FIELD_MAPPINGS.items():
                    value = row[column].strip()

                    if value == '':
                        continue

                    biovolumes_by_taxon[taxon_id][key] = value

                    if key == 'list':
                        biovolumes_by_taxon[taxon_id]['provider'] = value[:-4]

            size_class_info = {}
            for key, column in SIZE_CLASS_FIELD_MAPPINGS.items():
                value = row[column].strip()

                if value == '':
                    continue

                size_class_info[key] = value

            biovolumes_by_taxon[taxon_id]['size_classes'].append(size_class_info)

        # Part 2: Create or update Django models from dicts.
        for taxon_id, biovolumes in biovolumes_by_taxon.items():
            facts_dict = {
                'collection': collection,
                'provider': provider,
                'attributes': biovolumes,
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
                                'Skipping invalid %s biovolumes. Error(s) was: %s'
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
                'Successfully imported %s biovolumes for %u taxa.'
                % (provider, number_of_saved_objects)
            ))