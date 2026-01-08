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
        """Only show taxa that have image labeling images"""
        qs = super().get_queryset(request)

        # Filter to only taxa with image labeling images
        from media.models import ImageLabelingImage

        taxa_with_images = (
            ImageLabelingImage.objects.filter(attributes__imagelabeling=True)
            .values_list("taxon_id", flat=True)
            .distinct()
        )

        return qs.filter(id__in=taxa_with_images).order_by("scientific_name")

    def changelist_view(self, request, extra_context=None):
        """Add explanatory text about filtered taxa"""
        extra_context = extra_context or {}
        extra_context["subtitle"] = (
            "Only taxa with associated image labeling images are displayed. "
            "Add images through the Image Labeling Images admin to make "
            "a taxon appear here."
        )
        return super().changelist_view(request, extra_context)

    def has_module_permission(self, request):
        """Show in admin if user has the custom permission"""
        return request.user.has_perm("taxa.edit_image_labeling_description")

    def has_change_permission(self, request, obj=None):
        """Allow editing if user has the custom permission"""
        return request.user.has_perm("taxa.edit_image_labeling_description")
