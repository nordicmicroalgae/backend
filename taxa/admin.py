from typing import ClassVar

from django.contrib import admin
from django.utils.html import format_html

from .models import ImageLabelingTaxonDescription, OrphanedDescription


@admin.register(ImageLabelingTaxonDescription)
class ImageLabelingTaxonDescriptionAdmin(admin.ModelAdmin):
    list_display = ("scientific_name", "rank", "has_description", "has_images")  # UPDATED
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

    def has_images(self, obj):  # ADD THIS METHOD
        """Show if taxon has image labeling images"""
        from media.models import ImageLabelingImage

        return ImageLabelingImage.objects.filter(
            taxon_id=obj.id, attributes__imagelabeling=True
        ).exists()

    has_images.boolean = True
    has_images.short_description = "Has Images"

    def has_add_permission(self, request):
        return False  # Can only edit existing taxa

    def has_delete_permission(self, request, obj=None):
        return False  # Can't delete taxa from this interface

    def get_queryset(self, request):
        """Show taxa that have image labeling images OR descriptions"""
        qs = super().get_queryset(request)

        # Filter to taxa with image labeling images OR taxa with descriptions
        from django.db.models import Q

        from media.models import ImageLabelingImage

        taxa_with_images = (
            ImageLabelingImage.objects.filter(attributes__imagelabeling=True)
            .values_list("taxon_id", flat=True)
            .distinct()
        )

        return qs.filter(
            Q(id__in=taxa_with_images)
            | (
                Q(image_labeling_description__isnull=False)
                & ~Q(image_labeling_description="")
            )
        ).order_by("scientific_name")

    def changelist_view(self, request, extra_context=None):
        """Add explanatory text about filtered taxa"""
        extra_context = extra_context or {}
        extra_context["subtitle"] = (
            "Only taxa with image labeling images or descriptions are displayed. "
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


@admin.register(OrphanedDescription)
class OrphanedDescriptionAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = [
        "old_taxon_id",
        "description_preview",
        "updated_at",
    ]
    search_fields: ClassVar[list[str]] = ["old_taxon_id", "description"]
    readonly_fields: ClassVar[list[str]] = ["created_at", "updated_at"]
    actions: ClassVar[list[str]] = ["delete_selected"]

    def description_preview(self, obj):
        return (
            obj.description[:100] + "..."
            if len(obj.description) > 100
            else obj.description
        )

    description_preview.short_description = "Description"
