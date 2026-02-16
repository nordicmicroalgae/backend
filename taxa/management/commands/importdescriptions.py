import json

from django.core.management.base import BaseCommand

from taxa.models import OrphanedDescription, Taxon


class Command(BaseCommand):
    help = "Import taxon image labeling descriptions from JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            help="Path to descriptions JSON file.",
        )
        parser.add_argument(
            "-e",
            "--encoding",
            default="utf8",
            help='Encoding used in the JSON file. Default is "utf8".',
        )

    def handle(self, *args, **options):
        filepath = options["file"]
        encoding = options["encoding"]
        verbosity = options["verbosity"]

        loaded_records = []
        with open(filepath, "r", encoding=encoding) as infile:
            loaded_records = json.load(infile)

        if len(loaded_records) == 0:
            if verbosity > 0:
                self.stdout.write("No descriptions to import.")
            return

        number_of_restored_descriptions = 0
        number_of_orphaned_descriptions = 0

        for record in loaded_records:
            taxon_id = record["taxon_id"]
            description = record["image_labeling_description"]

            # Resolve the taxon relationship.
            try:
                taxon = Taxon.objects.get(pk=taxon_id)
                taxon.image_labeling_description = description
                taxon.save(update_fields=["image_labeling_description"])
                number_of_restored_descriptions += 1
            except Taxon.DoesNotExist:
                # Store as orphaned description
                OrphanedDescription.objects.update_or_create(
                    old_taxon_id=str(taxon_id), defaults={"description": description}
                )
                number_of_orphaned_descriptions += 1

                if verbosity > 1:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Could not find taxon with id '{taxon_id}'. "
                            f"Description stored as orphaned."
                        )
                    )

        if verbosity > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully imported "
                    f"{number_of_restored_descriptions} descriptions."
                )
            )
            if number_of_orphaned_descriptions > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"{number_of_orphaned_descriptions} orphaned "
                        f"descriptions stored in database."
                    )
                )
