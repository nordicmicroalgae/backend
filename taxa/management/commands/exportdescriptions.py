import json

from django.core.management.base import BaseCommand

from taxa.models import Taxon


class Command(BaseCommand):
    help = "Export taxon image labeling descriptions to JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--output",
            required=True,
            help="Path to output JSON file.",
        )
        parser.add_argument(
            "-e",
            "--encoding",
            default="utf8",
            help='Encoding for output file. Default is "utf8".',
        )

    def handle(self, *args, **options):
        output_path = options["output"]
        encoding = options["encoding"]
        verbosity = options["verbosity"]

        queryset = Taxon.objects.exclude(image_labeling_description="")

        records = []
        for taxon in queryset:
            records.append(
                {
                    "taxon_id": taxon.id,
                    "image_labeling_description": taxon.image_labeling_description,
                }
            )

        with open(output_path, "w", encoding=encoding) as outfile:
            json.dump(records, outfile, indent=2, ensure_ascii=False)

        if verbosity > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully exported %u descriptions." % len(records)
                )
            )
