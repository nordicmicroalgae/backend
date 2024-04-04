import csv


from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model


UserModel = get_user_model()


def get_representation(obj):
    return {
        'username': getattr(obj, UserModel.USERNAME_FIELD),
        'first_name': obj.first_name,
        'last_name': obj.last_name,
        'email': obj.email,
        'is_active': 'yes' if obj.is_active else 'no',
        'is_staff': 'yes' if obj.is_staff else 'no',
        'is_superuser': 'yes' if obj.is_superuser else 'no',
        'last_login': obj.last_login,
        'date_joined': obj.date_joined,
    }

def get_objects():
    queryset = UserModel.objects.order_by(
        UserModel.USERNAME_FIELD
    )
    yield from queryset.iterator()


class Command(BaseCommand):
    help = 'Export users to CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '-o',
            '--output',
            help='Path to file where output is written.',
        )

    def handle(self, *args, **options):
        output = options['output']

        self.stdout.ending = None

        try:
            stream = open(output, 'w') if output else self.stdout

            writer = None
            for obj in get_objects():
                representation = get_representation(obj)

                if writer is None:
                    writer = csv.DictWriter(
                        stream,
                        representation.keys(),
                        dialect='excel-tab'
                    )
                    writer.writeheader()

                writer.writerow(representation)
        except Exception as e:
            raise CommandError('Export failed: %s' % e)
        finally:
            if stream:
                stream.close()
