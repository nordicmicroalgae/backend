from os import path

from django.core.files.storage import FileSystemStorage
from django.utils.functional import cached_property


class MediaOriginFileStorage(FileSystemStorage):
    @cached_property
    def base_location(self):
        return path.join(super().base_location, "origins")

    @cached_property
    def base_url(self):
        return super().base_url + "origins/"


class MediaRenditionFileStorage(FileSystemStorage):
    pass


default_origin_storage = MediaOriginFileStorage()

default_rendition_storage = MediaRenditionFileStorage()
