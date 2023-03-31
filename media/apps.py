from django.apps import AppConfig
from django.db.models.signals import post_delete

from . import get_media_models


class MediaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'media'

    def ready(self):
        from .models import remove_file_on_delete

        # connect signal receivers to each model class as sender
        for media_model in get_media_models():
            dispatch_uid = (
                '%s.remove_file_on_delete'
                 % media_model.__name__.lower()
            )
            post_delete.connect(
                remove_file_on_delete,
                sender=media_model,
                dispatch_uid=dispatch_uid
            )
