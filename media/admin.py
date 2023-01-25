from django.contrib import admin

from media.models import Media, Image


class MediaAdmin(admin.ModelAdmin):
    pass

class ImageAdmin(MediaAdmin):
    pass


admin.site.register(Image, ImageAdmin)
