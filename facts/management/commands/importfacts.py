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

IOC = (
    Path(
        settings.CONTENT_DIR,
        'species', 'facts_hab_ioc.txt'
    ),
    dict(
        encoding='utf8',
        provider='IOC',
        collection='Harmful algae blooms',
        url_template='https://www.marinespecies.org/hab/aphia.php?p=taxdetails&id=<replace_id>',
        external_id_field='taxon_id',
        note_field='hab_effect',
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
        external_id_field='strain_name',
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
        id_field='AphiaID',
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
            call_command('importbiovolumes', nomp_file, verbosity=verbosity, **nomp_opts)

            algaebase_file, algaebase_opts = ALGAEBASE
            if verbosity > 0:
                self.stdout.write('Importing AlgaeBase external links...')
            call_command('importlinks', algaebase_file, verbosity=verbosity, **algaebase_opts)

            dyntaxa_file, dyntaxa_opts = DYNTAXA
            if verbosity > 0:
                self.stdout.write('Importing Dyntaxa external links...')
            call_command('importlinks', dyntaxa_file, verbosity=verbosity, **dyntaxa_opts)

            ioc_file, ioc_opts = IOC
            if verbosity > 0:
                self.stdout.write('Importing IOC external links...')
            call_command('importlinks', ioc_file, verbosity=verbosity, **ioc_opts)

            norcca_file, norcca_opts = NORCCA
            if verbosity > 0:
                self.stdout.write('Importing NORCCA external links...')
            call_command('importlinks', norcca_file, verbosity=verbosity, **norcca_opts)

            worms_file, worms_opts = WORMS
            if verbosity > 0:
                self.stdout.write('Importing WORMS external links...')
            call_command('importlinks', worms_file, verbosity=verbosity, **worms_opts)
