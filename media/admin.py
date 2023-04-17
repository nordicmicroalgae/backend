from django.contrib import admin
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.urls import path, reverse

from media.forms import ImageForm
from media.models import Image


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


class TaxonSelect(admin.widgets.AutocompleteSelect):
    """
    Select widget that loads options from MediaAdmin.taxon_options_json_view.

    Re-uses the built-in AutocompleteSelect widget but overrides the way the
    URL for the options endpoint is created by pointing to an URL for
    MediaAdmin.taxon_options_json_view instead of the default and more generic
    AutocompleteJsonView.

    This customization accomplishes two things:
      1. Bypass the requirement of registering the Taxon model in a ModelAdmin
         just for the solely purpose of making a list of name options available.
      2. Complete control over the view's implementation and further
         possibilities for creating different implementations for different
         media model types.
    """
    url_name = '%s:%s_%s_taxon_options'

    def __init__(self, field, admin_site, media_model, **kwargs):
        super().__init__(field, admin_site, **kwargs)
        self.model = media_model

    def get_url(self):
        return reverse(
            self.url_name % (
                self.admin_site.name,
                self.model._meta.app_label,
                self.model._meta.model_name,
            )
        )


class MediaAdmin(admin.ModelAdmin):
    list_display = ('slug', 'title', 'taxon')

    search_fields = (
        'attributes__title',
        'taxon__scientific_name',
    )

    list_filter = (TaxonListFilter,)

    def get_urls(self):
        urls = [
            path(
                'taxon_options',
                self.admin_site.admin_view(
                    self.taxon_options_json_view
                ),
                name='%s_%s_taxon_options' % (
                    self.model._meta.app_label,
                    self.model._meta.model_name
                )
            )
        ]
        return urls + super().get_urls()

    def taxon_options_json_view(self, request):
        term = request.GET.get('term', '')

        queryset = self.model.taxon.get_queryset()

        if len(term) == 0:
            queryset = queryset.all()
        else:
            queryset = queryset.filter(
                scientific_name__icontains=term
            )

        paginator = Paginator(queryset, 50)
        page = paginator.get_page(request.GET.get('page', 1))

        return JsonResponse({
            'results': [
                {'id': str(obj.id), 'text': str(obj)} for obj in page
            ],
            'pagination': {'more': page.has_next()}
        })

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        db = kwargs.get('using')

        if db_field.name == 'taxon':
            kwargs['widget'] = TaxonSelect(
                db_field,
                self.admin_site,
                self.model,
                using=db
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

    def get_ordering(self, request):
        is_filtered_by_taxon = (
            TaxonListFilter.parameter_name in request.GET
        )
        return ('priority',) if is_filtered_by_taxon else ('-created_at',)

    def save_model(self, request, obj, form, change):
        if not hasattr(obj, 'created_by'):
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

        if hasattr(obj, 'create_renditions') and callable(obj.create_renditions):
            obj.create_renditions()

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
