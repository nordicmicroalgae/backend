import csv
import json
import pathlib

from django.core.management.base import BaseCommand
from django.conf import settings

from facts.models import Facts
from taxa.models import Taxon
from core.utils import make_attribute_list


FACTS_DYNTAXA = pathlib.Path(
    settings.CONTENT_DIR,
    'species', 'taxa_dyntaxa.txt'
)

FACTS_ALGAEBASE = pathlib.Path(
    settings.CONTENT_DIR,
    'species', 'external_links_algaebase.txt'
)

FACTS_IOC_HAB = pathlib.Path(
    settings.CONTENT_DIR,
    'species', 'external_facts_ioc_hab.txt'
)

FACTS_OMNIDIA_CODES = pathlib.Path(
    settings.CONTENT_DIR,
    'species', 'external_facts_omnidia_codes.txt'
)

FACTS_REBECCA_CODES = pathlib.Path(
    settings.CONTENT_DIR,
    'species', 'external_facts_rebecca_codes.txt'
)

FACTS_HELCOM_PEG = pathlib.Path(
    settings.CONTENT_DIR,
    'species', 'peg_bvol2013.json'
)

FACTS_HELCOM_PEG_TRANSLATE = pathlib.Path(
    settings.CONTENT_DIR,
    'species', 'peg_to_dyntaxa.txt'
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
        #    keyed by scientific name
        prepared_facts = {}

        def prepare_facts(scientific_name, facts_dict):
            if scientific_name not in prepared_facts:
                prepared_facts[scientific_name] = []
            prepared_facts[scientific_name].append(facts_dict)


        # 1.1: Read and prepare Dyntaxa IDs from CSV
        #      Provider: Dyntaxa
        #      Collection: Dyntaxa IDs
        with FACTS_DYNTAXA.open('r', encoding='utf16') as in_file:
            rows = csv.DictReader(in_file, dialect='excel-tab')

            for row in rows:
                prepare_facts(row['Scientific name'], {
                    'provider': 'Dyntaxa',
                    'collection': 'Dyntaxa IDs',
                    'attributes': [{
                        'name': 'Dyntaxa ID',
                        'value': row['Dyntaxa id'],
                    }],
                })

        # 1.2: Read and prepare AlagaeBase IDs from CSV
        #      Provider: AlgaeBase
        #      Collection: AlgaeBase IDs
        with FACTS_ALGAEBASE.open('r', encoding='utf16') as in_file:
            rows = csv.DictReader(in_file, dialect='excel-tab')

            for row in rows:
                prepare_facts(row['Scientific name'], {
                    'provider': 'AlgaeBase',
                    'collection': 'AlgaeBase IDs',
                    'attributes': [{
                        'name': 'AlgaeBase ID',
                        'value': row['Algaebase id'],
                    }],
                })

        # 1.3: Read and prepare IOC Harmfulness from CSV
        #      Provider: IOC
        #      Collection: IOC Harmfulness
        with FACTS_IOC_HAB.open('r', encoding='utf16') as in_file:
            rows = csv.DictReader(in_file, dialect='excel-tab')

            for row in rows:
                prepare_facts(row['Scientific name'], {
                    'provider': 'IOC',
                    'collection': 'IOC Harmfulness',
                    'attributes': [{
                        'name': 'Harmfulness, IOC',
                        'value': row['Harmfulness, IOC'],
                    }],
                })

        # 1.4: Read and prepare OMNIDIA codes from CSV
        #      Provider: SLU
        #      Collection: OMNIDIA Codes
        with FACTS_OMNIDIA_CODES.open('r', encoding='utf16') as in_file:
            rows = csv.DictReader(in_file, dialect='excel-tab')

            for row in rows:
                prepare_facts(row['Scientific name'], {
                    'provider': 'SLU',
                    'collection': 'OMNIDIA Codes',
                    'attributes': [{
                        'name': 'OMNIDIA Code',
                        'value': row['OMNIDIA code'],
                    }],
                })

        # 1.5: Read and prepare REBECCA codes from CSV
        #      Provider: NIVA
        #      Collection: REBECCA Codes
        with FACTS_REBECCA_CODES.open('r', encoding='utf16') as in_file:
            rows = csv.DictReader(in_file, dialect='excel-tab')

            for row in rows:
                prepare_facts(row['AcceptedTaxon'], {
                    'provider': 'NIVA',
                    'collection': 'REBECCA Codes',
                    'attributes': [{
                        'name': 'REBECCA Code',
                        'value': row['RebeccaID'],
                    }],
                })

        # 1.6: Read and prepare HELCOM-PEG data from JSON (translations from CSV)
        #      Provider: HELCOM-PEG
        #      Collection: Biolvolumes
        peg_translate = {}

        with FACTS_HELCOM_PEG_TRANSLATE.open('r', encoding='utf16') as in_file:
            rows = csv.DictReader(in_file, dialect='excel-tab')

            peg_translate = {
                row['PEG taxon name']: row['DynTaxa taxon name']
                for row in rows
            }

        with FACTS_HELCOM_PEG.open('r', encoding='utf8') as in_file:
            items = json.load(in_file)

            for item in items:
                prepare_facts(
                    peg_translate.get(item['Species'], item['Species']), {
                        'provider': 'HELCOM-PEG',
                        'collection': 'Biovolumes',
                        'attributes': json.loads(
                            json.dumps(item),
                            object_hook=make_attribute_list
                        ),
                    }
                )


        # 2: Iterate over prepared facts and write to database
        for scientific_name, data in prepared_facts.items():
            # Integrity check
            try:
                taxon = Taxon.objects.get(pk=scientific_name)
            except Taxon.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                   'WARNING: Taxon name: "%s" not found in database. '
                   'Skipping import of facts.'
                   % scientific_name
                ))
                continue

            facts = Facts(taxon=taxon,data=data)
            facts.save()


        number_of_created_rows = Facts.objects.all().count()

        self.stdout.write(self.style.SUCCESS(
            'Successfully imported facts for %d species.' % number_of_created_rows
        ))
