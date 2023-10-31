import csv
import secrets
import string

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.dateparse import parse_datetime


UserModel = get_user_model()


def to_boolean(value):
    return str(value).lower() in ['true', 'yes']

def make_password(length=64):
    allowed_chars = string.ascii_letters + string.digits
    return ''.join(
        secrets.choice(allowed_chars) for _ in range(length)
    )

def add_users_to_group(*users, group):
    group, _ = Group.objects.get_or_create(name=group)
    group.user_set.add(*users)


class UserWillBeRemoved(Exception):
    pass


class Command(BaseCommand):
    help = 'Import users from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            help='Path to users CSV file.',
        )
        parser.add_argument(
            '-c',
            '--clear',
            action='store_true',
            help=(
                'Clear any existing users from '
                'database before writing new ones.'
            ),
        )
        parser.add_argument(
            '-e',
            '--encoding',
            default='utf8',
            help=(
                'Encoding used in the users '
                'CSV file. Default is "utf8".'
            ),
        )

    def handle(self, *args, **options):
        filepath = options['file']
        encoding = options['encoding']
        clear_existing_users = options['clear']
        verbosity = options['verbosity']

        users_to_create = []
        users_to_update = []

        # Part 1: Load rows from CSV file and convert to Django models.
        user_rows = []
        with open(filepath, 'r', encoding=encoding) as in_file:
            user_rows = list(csv.DictReader(in_file, dialect='excel-tab'))

        if len(user_rows) == 0:
            raise CommandError(
                'Found zero records in specified CSV file. Aborting.'
            )

        for user_row in user_rows:
            username = user_row['username']
            try:
                user = UserModel.objects.get(
                    **{UserModel.USERNAME_FIELD: username}
                )
                if clear_existing_users:
                    raise UserWillBeRemoved()
                users_to_update.append(user)
            except(UserModel.DoesNotExist, UserWillBeRemoved):
                user = UserModel(
                    **{UserModel.USERNAME_FIELD: username}
                )
                user.set_password(make_password())
                users_to_create.append(user)

            user.first_name = user_row.get('first_name')
            user.last_name = user_row.get('last_name')
            user.email = user_row.get('email')

            user.is_active = to_boolean(
                user_row.get('is_active', 'yes')
            )
            user.is_staff = to_boolean(
                user_row.get('is_staff', 'yes')
            )
            user.is_superuser = to_boolean(
                user_row.get('is_superuser', 'no')
            )

            last_login = parse_datetime(
                user_row.get('last_login', '')
            )
            if last_login is not None:
                user.last_login = last_login

            date_joined = parse_datetime(
                user_row.get('date_joined', '')
            )
            if date_joined is not None:
                user.date_joined = date_joined


        # Part 2: Write created models in one atomic operation.
        number_of_created_users = 0
        number_of_updated_users = 0

        try:
            with transaction.atomic(savepoint=False):
                if clear_existing_users:
                    UserModel.objects.all().delete()

                for user_to_create in users_to_create:
                    user_to_create.save(force_insert=True)
                    number_of_created_users = number_of_created_users + 1

                for user_to_update in users_to_update:
                    user_to_update.save(force_update=True)
                    number_of_updated_users = number_of_updated_users + 1

                saved_users = users_to_create + users_to_update
                add_users_to_group(*saved_users, group='contributor')

        except Exception as e:
            raise CommandError(
                'Failed to write to database. '
                'Import aborted. Error was %s' % e
            )

        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS(
                'Successfully imported %u users '
                '(%u created and %u updated)' % (
                    number_of_created_users + number_of_updated_users,
                    number_of_created_users,
                    number_of_updated_users
                )
            ))
