from django.contrib import admin

from media.forms import MediaForm, ImageForm
from media.models import Media, Image


class MediaAdmin(admin.ModelAdmin):
    pass

class ImageAdmin(MediaAdmin):
    form = ImageForm
    pass


admin.site.register(Image, ImageAdmin)
