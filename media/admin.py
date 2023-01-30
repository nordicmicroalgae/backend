from django.contrib import admin

from media.forms import MediaForm, ImageForm
from media.models import Media, Image


class MediaAdmin(admin.ModelAdmin):
    pass

class ImageAdmin(MediaAdmin):
    form = ImageForm

    list_display = ('slug', 'title', 'taxon')



admin.site.register(Image, ImageAdmin)
