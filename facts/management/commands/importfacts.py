import csv
import pathlib

from django.core.management.base import BaseCommand
from django.conf import settings

from facts.models import Facts
from taxa.models import Taxon


FACTS_HELCOM_PEG = pathlib.Path(
    settings.CONTENT_DIR,
    'species', 'facts_biovolumes_nomp.txt'
)


class Command(BaseCommand):
    help = 'Import facts from CSV files'

    def handle(self, *args, **options):
        number_of_existing_rows = Facts.objects.all().count()

        # Clear existing facts
        if number_of_existing_rows > 0:
            self.stdout.write('Clearing existing records from database...', ending='')
            Facts.objects.all().delete()
            self.stdout.write(' done.')

        # 1: Start by preparing lists of facts from various sources,
        #    keyed by taxon identifier
        prepared_facts = {}

        def prepare_facts(taxon_id, facts_dict):
            if taxon_id not in prepared_facts:
                prepared_facts[taxon_id] = []
            prepared_facts[taxon_id].append(facts_dict)

        # 1.1: Read and prepare HELCOM-PEG data from CSV
        #      Provider: HELCOM-PEG
        #      Collection: Biolvolumes
        with FACTS_HELCOM_PEG.open('r', encoding='cp1252') as in_file:
            rows = csv.DictReader(in_file, dialect='excel-tab')

            general_fields_mappings = {
                'Division': 'division',
                'Class': 'class',
                'Order': 'order',
                'Genus': 'genus',
                'Species': 'species',
                'SFLAG': 'sflag',
                'Author': 'authority',
                'Trophy': 'trophy',
                'Geometric_shape': 'geometric_shape',
                'FORMULA': 'formula',
            }

            size_class_fields_mappings = {
                'SizeClassNo': 'size_class_no',
                'Nonvalid_SIZCL': 'non_valid_size_class',
                'Unit': 'unit',
                'SizeRange': 'size_range',
                'Length(l1)µm': 'length1',
                'Length(l2)µm': 'length2',
                'Width(w)µm': 'width',
                'Height(h)µm': 'height',
                'Diameter(d1)µm': 'diameter1',
                'Diameter(d2)µm': 'diameter2',
                'No_of_cells/counting_unit': 'no_of_cells_per_counting_unit',
                'Calculated_volume_µm3': 'calculated_volume',
                'Comment': 'comment',
                'Filament_length_of_cell(µm)': 'filament_lengt_of_cell',
                'Calculated_Carbon_pg/counting_unit': 'calculated_carbon_pg_per_counting_unit',
                'Comment_on_Carbon_calculation': 'comment_on_carbon_calculation',
                'STAGE': 'stage',
            }

            biovolumes_by_id = {}

            for row in rows:

                if row['AphiaID'] == '':
                    self.stdout.write(self.style.WARNING(
                        'WARNING: Missing AphiaID for: %s. Skipping row.'% ' -> '.join(
                            [row[col] for col in ['Class', 'Order', 'Genus', 'Species']
                        ])))
                    continue

                if not row['AphiaID'] in biovolumes_by_id.keys():
                    biovolumes_by_id[row['AphiaID']] = {
                        'size_classes': [],
                    }

                    for column, key in general_fields_mappings.items():
                        value = row[column].strip()

                        if value == '':
                            continue

                        biovolumes_by_id[row['AphiaID']][key] = value


                size_class_info = {}
                for column, key in size_class_fields_mappings.items():
                    value = row[column].strip()

                    if value == '':
                        continue

                    size_class_info[key] = value

                biovolumes_by_id[row['AphiaID']]['size_classes'].append(size_class_info)


            for taxon_id, biovolumes in biovolumes_by_id.items():
                prepare_facts(taxon_id, {
                    'provider': 'HELCOM-PEG',
                    'collection': 'Biovolumes',
                    'attributes': biovolumes,
                })



        # 2: Iterate over prepared facts and write to database
        for taxon_id, data in prepared_facts.items():
            # Integrity check
            try:
                taxon = Taxon.objects.get(pk=taxon_id)
            except Taxon.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                   'WARNING: Taxon with id: "%s" not found in database. '
                   'Skipping import of facts.'
                   % taxon_id
                ))
                continue

            facts = Facts(taxon=taxon,data=data)
            facts.save()

        number_of_created_rows = Facts.objects.all().count()

        self.stdout.write(self.style.SUCCESS(
            'Successfully imported facts for %d species.' % number_of_created_rows
        ))
