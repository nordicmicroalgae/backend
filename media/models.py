import os
import itertools

from django.db import models
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.text import slugify


from media import renditions
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

def available_priorities(taxon=None):
    incrementing_priority = itertools.count(0)

    preexisting_priorities = (
        Media.objects.filter(taxon=taxon).values_list('priority', flat=True)
    )

    return filter(
        lambda p: p not in preexisting_priorities,
        incrementing_priority
    )

def primary_path_for_media(instance, filename):
    _file_root, file_ext = os.path.splitext(filename)
    return str(instance.slug) + str(file_ext)


class MediaManager(models.Manager):
    pass

class ImageManager(MediaManager):
    def get_queryset(self):
        return super().get_queryset().filter(type__startswith='image/')


class Media(models.Model, renditions.ModelActionsMixin):
    taxon = models.ForeignKey(
        Taxon,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    priority = models.IntegerField(editable=False)

    slug = models.SlugField(editable=False, max_length=255, unique=True)
    file = models.FileField(upload_to=primary_path_for_media)
    type = models.CharField(max_length=32)

    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(editable=False, auto_now=True)

    attributes = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    renditions = models.JSONField(default=dict)

    objects = MediaManager()

    class Meta:
        unique_together = ('taxon', 'priority')

    @property
    def title(self):
        return self.attributes.get('title', 'Untitled')

    def save(self, *args, **kwargs):
        if not self.slug:
            setattr(self, 'slug', next(available_slugs(self.title)))
        if self.priority is None:
            setattr(self, 'priority', next(available_priorities(self.taxon)))

        return super().save(*args, **kwargs)

@renditions.register(
    s=(renditions.ResizedImage, 240, 240),
    m=(renditions.ResizedImage, 480, 480),
    l=(renditions.ResizedImage, 1024, 1024),
)
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
