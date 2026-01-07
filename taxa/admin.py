from django.contrib import admin
from django.utils.html import format_html

from .models import ImageLabelingTaxonDescription


@admin.register(ImageLabelingTaxonDescription)
class ImageLabelingTaxonDescriptionAdmin(admin.ModelAdmin):
    list_display = ("scientific_name", "rank", "has_description")
    list_filter = ("rank",)
    search_fields = ("scientific_name", "slug")

    fields = ("taxon_info", "image_labeling_description")
    readonly_fields = ("taxon_info",)

    def taxon_info(self, obj):
        """Display taxon information as read-only"""
        info_parts = [f"<strong style='font-size: 14px;'>{obj.scientific_name}</strong>"]
        if obj.authority:
            info_parts.append(f"<span style='color: #666;'>{obj.authority}</span>")
        if obj.rank:
            info_parts.append(
                f"<div style='margin-top: 5px;'><em>Rank: {obj.rank}</em></div>"
            )
        info_parts.append(f"<div><em>Slug: {obj.slug}</em></div>")
        return format_html("<br>".join(info_parts))

    taxon_info.short_description = "Taxon"

    def has_description(self, obj):
        """Show if description exists"""
        return bool(obj.image_labeling_description)

    has_description.boolean = True
    has_description.short_description = "Has Description"

    def has_add_permission(self, request):
        return False  # Can only edit existing taxa

    def has_delete_permission(self, request, obj=None):
        return False  # Can't delete taxa from this interface

    def get_queryset(self, request):
        """Order by scientific name"""
        qs = super().get_queryset(request)
        return qs.order_by("scientific_name")

    def has_module_permission(self, request):
        """Show in admin if user has the custom permission"""
        return request.user.has_perm("taxa.edit_image_labeling_description")

    def has_change_permission(self, request, obj=None):
        """Allow editing if user has the custom permission"""
        return request.user.has_perm("taxa.edit_image_labeling_description")
