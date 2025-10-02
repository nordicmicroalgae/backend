import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder

from media.models import Media

UserModel = get_user_model()


def get_representation(obj):
    return {
        "taxon": getattr(obj.taxon, "pk", None),
        "priority": obj.priority,
        "slug": obj.slug,
        "file": str(obj.file),
        "type": obj.type,
        "created_by": getattr(obj.created_by, UserModel.USERNAME_FIELD),
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
        "attributes": obj.attributes,
        "renditions": obj.renditions,
    }


def get_objects():
    queryset = Media.objects.order_by("taxon", "priority")
    yield from queryset.iterator()


class Command(BaseCommand):
    help = "Export media records to JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--output",
            help="Path to file where output is written.",
        )
        parser.add_argument(
            "-i",
            "--indent",
            type=int,
            default=2,
            help="Indentation level used for pretty-printing.",
        )

    def handle(self, *args, **options):
        output = options["output"]
        indent = options["indent"]

        json_dump_options = {
            "indent": indent,
            "cls": DjangoJSONEncoder,
        }

        self.stdout.ending = None

        try:
            stream = open(output, "w") if output else self.stdout

            stream.write("[")

            is_first_object = True
            for obj in get_objects():
                if not is_first_object:
                    stream.write(",\n")

                representation = get_representation(obj)
                json.dump(representation, stream, **json_dump_options)

                is_first_object = is_first_object and False

            stream.write("]\n")
        except Exception as e:
            raise CommandError("Export failed: %s." % e)
        finally:
            if stream:
                stream.close()
