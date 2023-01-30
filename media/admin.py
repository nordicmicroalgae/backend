from django.contrib import admin

from media.forms import MediaForm, ImageForm
from media.models import Media, Image


class TaxonListFilter(admin.SimpleListFilter):
    title = 'taxon'
    parameter_name = 'taxon'

    def lookups(self, request, model_admin):
        qs = model_admin.model.objects.filter(
            created_by=request.user
        ).distinct(
            'taxon__scientific_name'
        ).values_list(
            'taxon__id',
            'taxon__scientific_name'
        )
        return list(
            map(lambda row: (str(row[0]), str(row[1])), qs)
        )

    def queryset(self, request, queryset):
        taxon_id = self.value()
        if taxon_id is not None:
            if taxon_id.lower() == 'none':
                taxon_id = None
            return queryset.filter(taxon=taxon_id)
        return queryset


class MediaAdmin(admin.ModelAdmin):
    list_display = ('slug', 'title', 'taxon')

    search_fields = (
        'attributes__title',
        'taxon__scientific_name',
    )

    list_filter = (TaxonListFilter,)

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ImageAdmin(MediaAdmin):
    form = ImageForm


admin.site.register(Image, ImageAdmin)
