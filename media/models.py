import itertools

from django.db import models
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
    file = models.FileField()
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
