import json

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from media.models import Media
from taxa.models import Taxon


UserModel = get_user_model()


class Command(BaseCommand):
    help = 'Import media records from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            help='Path to media records JSON file.',
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
            default='utf8',
            help=(
                'Encoding used in the records '
                'JSON file. Default is "utf8".'
            ),
        )

    def handle(self, *args, **options):
        filepath = options['file']
        encoding = options['encoding']
        clear_existing_objects = options['clear']
        verbosity = options['verbosity']

        objects_to_save = []

        # Part 1: Load records from JSON file and convert to Django models.
        loaded_records = []
        with open(filepath, 'r', encoding=encoding) as infile:
            loaded_records = json.load(infile)

        if len(loaded_records) == 0:
            raise CommandError(
                'Found zero records in specified JSON file. Aborting.'
            )

        for loaded_record in loaded_records:
            object_args = {**loaded_record}

            # Resolve the taxon relationship.
            taxon_id = object_args.pop('taxon', None)
            try:
                object_args['taxon'] = Taxon.objects.get(pk=taxon_id)
            except Taxon.DoesNotExist:
                if verbosity > 1:
                    self.stdout.write(self.style.WARNING(
                        "Could not find taxon with id '%s'. "
                        "The record will still be imported but "
                        "it's relation to a taxon will be lost."
                        % taxon_id
                    ))
                object_args['taxon'] = None

            # Resolve the creator/user relationship.
            created_by_name = object_args.pop('created_by', None)
            try:
                object_args['created_by'] = UserModel.objects.get(
                    **{UserModel.USERNAME_FIELD: created_by_name}
                )
            except UserModel.DoesNotExist:
                raise CommandError(
                    'Failed to resolve creator for media object. '
                    'There is no user named "%s" in the database. Aborting.'
                    % created_by_name
                )

            created_object = Media(**object_args)
            objects_to_save.append(created_object)


        # Part 2: Write the created models in one atomic operation.
        number_of_saved_objects = 0

        try:
            with transaction.atomic(savepoint=False):
                if clear_existing_objects:
                    Media.objects.all().delete()

                for object_to_save in objects_to_save:
                    object_to_save.save()
                    number_of_saved_objects = number_of_saved_objects + 1
        except Exception as e:
            raise CommandError(
                'Failed to write to database. '
                'Import aborted. Error was: %s' % e
            )

        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS(
                'Successfully imported %u objects.'
                % number_of_saved_objects
            ))
