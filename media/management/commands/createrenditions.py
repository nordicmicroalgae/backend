from django.core.management.base import BaseCommand, CommandError

from media.renditions import get_registered_models


def get_registered_models_by_name():
    return {
        cls.__name__.lower(): cls
        for cls in get_registered_models()
    }


class Command(BaseCommand):
    help = (
        'Generate all kind of file representations '
        '(e.g. thumbnails), for all kind of Media objects.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'args',
            metavar='model_names',
            nargs='*',
            help=(
                'Name of model classes to create renditions for. '
                'Should be all lowercase. If this is not provided, '
                'all registered model classes will be used.'
            ),
        )

    def handle(self, *model_names, **options):
        verbosity = options['verbosity']

        registered_models = get_registered_models_by_name()

        model_names = model_names or registered_models.keys()

        model_classes = []

        for model_name in model_names:
            if model_name not in registered_models:
                raise CommandError(
                    "Failed to resolve model with name '%s'. "
                    "Please provide one or more of: '%s' instead."
                    % (model_name, "','".join(registered_models.keys()))
                )

            model_classes.append(registered_models.get(model_name))


        number_of_processed_objects = 0

        for model_class in model_classes:
            queryset = model_class.objects.all()
            total_count = queryset.count()

            for count, obj in enumerate(queryset, start=1):
                if verbosity > 0:
                    self.stdout.write(
                        "Processing '%s' %u of %u."
                        % (model_class.__name__, count, total_count)
                    )

                obj.create_renditions()
                obj.file.close()

                number_of_processed_objects = (
                    number_of_processed_objects + 1
                )

        if verbosity > 0:
            self.stdout.write(self.style.SUCCESS(
                'Successfully processed %u objects.'
                % number_of_processed_objects
            ))
