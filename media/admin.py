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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

    def save_model(self, request, obj, form, change):
        if not hasattr(obj, 'created_by'):
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def add_view(self, request, form_url='', extra_context=False):
        extra_context = self._extra_context_with_defaults(extra_context)
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=False):
        extra_context = self._extra_context_with_defaults(extra_context)
        return super().change_view(request, object_id, form_url, extra_context)

    def _extra_context_with_defaults(self, extra_context):
        return {
            'show_save_and_continue': False,
            'show_save_and_add_another': False,
            **(extra_context or {})
        }

class ImageAdmin(MediaAdmin):
    form = ImageForm


admin.site.register(Image, ImageAdmin)
