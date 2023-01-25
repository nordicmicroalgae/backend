from django.db import models
from django.contrib.auth import get_user_model


from taxa.models import Taxon


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

    slug = models.SlugField(editable=False, max_length=255)
    file = models.FileField()
    type = models.CharField(max_length=32)

    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)
    updated_at = models.DateTimeField(editable=False, auto_now=True)
    sort_order = models.IntegerField()

    attributes = models.JSONField(default=dict)

    objects = MediaManager()

class Image(Media):
    objects = ImageManager()

    class Meta:
        proxy = True
