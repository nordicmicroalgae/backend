import os
import itertools

from django.db import models
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.text import slugify


from taxa.models import Taxon


def available_slugs(name_base='untitled'):
    slug_mask = slugify(name_base) + '-%d'

    def incrementing_slugs():
        counter = itertools.count(1)
        for number in counter:
            yield slug_mask % number

    preexisting_slugs = (
        Media.objects.all().values_list('slug', flat=True)
    )

    return filter(
        lambda s: s not in preexisting_slugs,
        incrementing_slugs()
    )

def primary_path_for_media(instance, filename):
    _file_root, file_ext = os.path.splitext(filename)
    return str(instance.slug) + str(file_ext)


class MediaManager(models.Manager):
    pass

class ImageManager(MediaManager):
    def get_queryset(self):
        return super().get_queryset().filter(type__startswith='image/')



class Media(models.Model):
    taxon = models.ForeignKey(
        Taxon,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    slug = models.SlugField(editable=False, max_length=255, unique=True)
    file = models.FileField(upload_to=primary_path_for_media)
    type = models.CharField(max_length=32)

    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(editable=False, auto_now=True)
    sort_order = models.IntegerField()

    attributes = models.JSONField(default=dict)

    objects = MediaManager()

    @property
    def title(self):
        return self.attributes.get('title', 'Untitled')

    def save(self, *args, **kwargs):
        if not self.slug:
            setattr(self, 'slug', next(available_slugs(self.title)))

        return super().save(*args, **kwargs)

class Image(Media):
    objects = ImageManager()

    class Meta:
        proxy = True


@receiver(models.signals.post_delete, sender=Image)
def remove_file_on_delete(sender, instance, **kwargs):
    if not instance.file:
        return

    if hasattr(instance.file, 'delete') and callable(instance.file.delete):
        instance.file.delete(save=False)
