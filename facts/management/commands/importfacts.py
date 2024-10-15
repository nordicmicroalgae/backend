from pathlib import Path


from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction


from facts.models import Facts


ALGAEBASE = (
    Path(
        settings.CONTENT_DIR,
        'species', 'facts_external_links_algaebase.txt'
    ),
    dict(
        encoding='iso-8859-1',
        provider='AlgaeBase',
        url_template='url',
        external_id_field='ab_id',
    )
)

DYNTAXA = (
    Path(
        settings.CONTENT_DIR,
        'species', 'facts_external_links_dyntaxa.txt'
    ),
    dict(
        encoding='iso-8859-1',
        provider='Dyntaxa',
        url_template='https://namnochslaktskap.artfakta.se/taxa/<replace_id>/details',
        external_id_field='dyntaxa_id',
    )
)

ENA = (
    Path(
        settings.CONTENT_DIR,
        'species', 'facts_external_links_ena.txt'
    ),
    dict(
        encoding='utf8',
        provider='ENA',
        url_template='url',
        external_id_field='ncbi_id',
    )
)

GBIF = (
    Path(
        settings.CONTENT_DIR,
        'species', 'facts_external_links_gbif.txt'
    ),
    dict(
        encoding='utf8',
        provider='GBIF',
        url_template='url',
        external_id_field='usage_key',
        note_field='n_nordic_occurrences',
    )
)

ITIS = (
    Path(
        settings.CONTENT_DIR,
        'species', 'facts_external_links_itis.txt'
    ),
    dict(
        encoding='utf8',
        provider='ITIS',
        url_template='url',
        external_id_field='itis_id',
    )
)

IOC = (
    Path(
        settings.CONTENT_DIR,
        'species', 'facts_external_links_hab_ioc.txt'
    ),
    dict(
        encoding='utf8',
        provider='IOC',
        collection='Harmful algae blooms',
        url_template='https://www.marinespecies.org/hab/aphia.php?p=taxdetails&id=<replace_id>',
        label_template='IOC HAB',
        external_id_field='taxon_id',
    )
)

IOC_UNESCO = (
    Path(
        settings.CONTENT_DIR,
        'species', 'facts_ioc_toxins.txt'
    ),
    dict(
        encoding='utf8',
        provider='IOC-UNESCO',
        collection='Harmful algae blooms',
        url_template='url',
        label_template='IOC Toxin: {recommended_acronym}',
        external_id_field='taxon_id',
    )
)

NCBI = (
    Path(
        settings.CONTENT_DIR,
        'species', 'facts_external_links_ncbi.txt'
    ),
    dict(
        encoding='utf8',
        provider='NCBI',
        url_template='url',
        external_id_field='ncbi_id',
    )
)

NORCCA = (
    Path(
        settings.CONTENT_DIR,
        'species', 'facts_external_links_norcca.txt'
    ),
    dict(
        encoding='utf8',
        provider='NORCCA',
        collection='Culture collection',
        url_template='strain_link',
        label_template='NORCCA (strain {strain_name})',
        external_id_field='strain_name',
    )
)

PR2 = (
    Path(
        settings.CONTENT_DIR,
        'species', 'facts_external_links_pr2.txt'
    ),
    dict(
        encoding='utf8',
        provider='PR2',
        url_template='url',
        label_template='PR2: {pr2_name}',
        external_id_field='pr2_name',
    )
)

WORMS = (
    Path(
        settings.CONTENT_DIR,
        'species', 'facts_external_links_worms.txt'
    ),
    dict(
        encoding='utf8',
        provider='WoRMS',
        url_template='https://www.marinespecies.org/aphia.php?p=taxdetails&id=<replace_id>',
        external_id_field='taxon_id',
    )
)

NOMP = (
    Path(
        settings.CONTENT_DIR,
        'species', 'facts_biovolumes_nomp.txt'
    ),
    dict(
        encoding='utf_8_sig',
        provider='NOMP',
        id_field='taxon_id',
    )
)


class Command(BaseCommand):
    help = 'Import facts from various sources'

    def handle(self, *args, **options):
        verbosity = options['verbosity']

        with transaction.atomic(savepoint=False):
            Facts.objects.all().delete()

            nomp_file, nomp_opts = NOMP
            if verbosity > 0:
                self.stdout.write('Importing NOMP biovolumes...')
            call_command('importbiovolumes', nomp_file, **{**options, **nomp_opts})

            algaebase_file, algaebase_opts = ALGAEBASE
            if verbosity > 0:
                self.stdout.write('Importing AlgaeBase external links...')
            call_command('importlinks', algaebase_file, **{**options, **algaebase_opts})

            dyntaxa_file, dyntaxa_opts = DYNTAXA
            if verbosity > 0:
                self.stdout.write('Importing Dyntaxa external links...')
            call_command('importlinks', dyntaxa_file, **{**options, **dyntaxa_opts})

            ena_file, ena_opts = ENA
            if verbosity > 0:
                self.stdout.write('Importing ENA external links...')
            call_command('importlinks', ena_file, **{**options, **ena_opts})

            gbif_file, gbif_opts = GBIF
            if verbosity > 0:
                self.stdout.write('Importing GBIF external links...')
            call_command('importlinks', gbif_file, **{**options, **gbif_opts})

            itis_file, itis_opts = ITIS
            if verbosity > 0:
                self.stdout.write('Importing ITIS external links...')
            call_command('importlinks', itis_file, **{**options, **itis_opts})

            ioc_file, ioc_opts = IOC
            if verbosity > 0:
                self.stdout.write('Importing IOC external links...')
            call_command('importlinks', ioc_file, **{**options, **ioc_opts})

            ioc_unesco_file, ioc_unesco_opts = IOC_UNESCO
            if verbosity > 0:
                self.stdout.write('Importing IOC-UNESCO external links...')
            call_command('importlinks', ioc_unesco_file, **{**options, **ioc_unesco_opts})

            ncbi_file, ncbi_opts = NCBI
            if verbosity > 0:
                self.stdout.write('Importing NCBI external links...')
            call_command('importlinks', ncbi_file, **{**options, **ncbi_opts})

            norcca_file, norcca_opts = NORCCA
            if verbosity > 0:
                self.stdout.write('Importing NORCCA external links...')
            call_command('importlinks', norcca_file, **{**options, **norcca_opts})

            worms_file, worms_opts = WORMS
            if verbosity > 0:
                self.stdout.write('Importing WORMS external links...')
            call_command('importlinks', worms_file, **{**options, **worms_opts})

            pr2_file, pr2_opts = PR2
            if verbosity > 0:
                self.stdout.write('Importing PR2 external links...')
            call_command('importlinks', pr2_file, **{**options, **pr2_opts})
