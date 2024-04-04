import os
import itertools

from django.db import models
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.text import slugify
from django.utils import timezone


from media import renditions
from media.storage import default_origin_storage
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


class InvalidTagset(Exception):
    pass

class Tag(models.Func):
    tagsets = (
        'contrast_enhancement',
        'galleries',
        'preservation',
        'stain',
        'technique',
    )

    function = 'JSONB_ARRAY_ELEMENTS_TEXT'

    def __init__(self, tagset):
        if tagset not in self.tagsets:
            raise InvalidTagset(
                'Expected one of: "%s", but got "%s".'
                % ('","'.join(self.tagsets), tagset)
            )

        super().__init__(models.F('attributes__%s' % tagset))


class MediaManager(models.Manager):
    def get_tagset(self, tagset):
        annotated_qs = self.get_queryset().annotate(name=Tag(tagset))
        return annotated_qs.values('name').order_by('name').distinct()

class ImageManager(MediaManager):
    def get_queryset(self):
        return super().get_queryset().filter(type__startswith='image/')


class Media(models.Model, renditions.ModelActionsMixin):
    taxon = models.ForeignKey(
        Taxon,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    priority = models.IntegerField(editable=False)

    slug = models.SlugField(editable=False, max_length=255, unique=True)

    file = models.FileField(
        upload_to=primary_path_for_media,
        storage=default_origin_storage,
    )

    type = models.CharField(max_length=32)

    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    attributes = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    renditions = models.JSONField(default=dict)

    objects = MediaManager()

    class Meta:
        db_table = 'taxon_media'

        constraints = [
            models.UniqueConstraint(
                fields=['taxon', 'priority'],
                name='unique_media_priority',
                deferrable=models.Deferrable.DEFERRED
            ),
        ]

        permissions = [
            ('manage_others', 'Can manage others media'),
        ]

    @property
    def title(self):
        return self.attributes.get('title', 'Untitled')

    def save(self, *args, **kwargs):
        if not self.slug:
            setattr(self, 'slug', next(available_slugs(self.title)))
        if self.priority is None:
            setattr(self, 'priority', next(available_priorities(self.taxon)))

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title

@renditions.register(
    o=(renditions.Image,),
    p=(renditions.EmbededPreviewImage,),
    s=(renditions.ResizedImage, 240, 240),
    m=(renditions.ResizedImage, 480, 480),
    l=(renditions.ResizedImage, 1024, 1024),
)
class Image(Media):
    objects = ImageManager()

    class Meta:
        proxy = True


# Signal receivers. Connected to senders in MediaConfig ready.
def remove_file_on_delete(sender, instance, **kwargs):
    if not instance.file:
        return

    if hasattr(instance.file, 'delete') and callable(instance.file.delete):
        instance.file.delete(save=False)
