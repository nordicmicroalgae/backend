import json
from typing import ClassVar

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from media.forms import ImageForm, ImageLabelingImageForm
from media.models import Image, ImageLabelingImage
from taxa.models import Taxon


class InvalidPriorityListJson(Exception):
    pass


class TagListFilter(admin.SimpleListFilter):
    def lookups(self, request, model_admin):
        qs = model_admin.model.objects.get_tagset(self.parameter_name)

        if not request.user.has_perm("media.manage_others"):
            qs = qs.filter(created_by=request.user)

        return list(
            map(lambda tag: (str(tag), str(tag)), qs.values_list("name", flat=True))
        )

    def queryset(self, request, queryset):
        tag_value = self.value()
        if tag_value is not None:
            queryset = queryset.filter(
                attributes__contains={self.parameter_name: [tag_value]}
            )
        return queryset

    @classmethod
    def factory(cls, parameter_name):
        title = parameter_name.replace("_", " ")

        class_name = "%sListFilter" % "".join(map(str.title, parameter_name.split("_")))
        class_attr = dict(title=title, parameter_name=parameter_name)

        return type(class_name, (cls,), class_attr)


class TaxonListFilter(admin.SimpleListFilter):
    title = "taxon"
    parameter_name = "taxon"

    def lookups(self, request, model_admin):
        qs = model_admin.model.objects
        if not request.user.has_perm("media.manage_others"):
            qs = qs.filter(created_by=request.user)

        qs = qs.distinct("taxon__scientific_name").values_list(
            "taxon__id", "taxon__scientific_name"
        )

        return list(map(lambda row: (str(row[0]), str(row[1])), qs))

    def queryset(self, request, queryset):
        taxon_id = self.value()
        if taxon_id is not None:
            taxon_id = self.normalize_value(taxon_id)
            return queryset.filter(taxon=taxon_id)
        return queryset

    @classmethod
    def normalize_value(cls, value):
        if str(value).lower() == "none":
            value = None
        return value


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

    url_name = "%s:%s_%s_taxon_options"

    def __init__(self, field, admin_site, media_model, **kwargs):
        super().__init__(field, admin_site, **kwargs)
        self.model = media_model

    def get_url(self):
        return reverse(
            self.url_name
            % (
                self.admin_site.name,
                self.model._meta.app_label,
                self.model._meta.model_name,
            )
        )


class MediaAdmin(admin.ModelAdmin):
    class Media:
        css: ClassVar[dict] = {
            "screen": (
                "admin/css/media_preview.css",
                "admin/css/media_priority.css",
            )
        }

    list_display = ("preview", "title", "taxon", "priority_actions")

    search_fields = (
        "attributes__title",
        "taxon__scientific_name",
    )

    list_filter = (
        TaxonListFilter,
        TagListFilter.factory("galleries"),
        TagListFilter.factory("contrast_enhancement"),
        TagListFilter.factory("preservation"),
        TagListFilter.factory("stain"),
        TagListFilter.factory("technique"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_priority_sorting = False

    def preview(self, obj):
        return format_html(
            '<div class="preview-container">'
            '  <div class="preview preview-{}">{}</div>'
            "</div>",
            self.model._meta.model_name,
            self.get_preview_html(obj),
        )

    def get_preview_html(self, obj):
        return format_html('<span class="not-available">?</span>')

    @admin.display(ordering="priority", description="Priority")
    def priority_actions(self, obj):
        boolean_attrs = "disabled" if not self.enable_priority_sorting else ""
        return format_html(
            '<div class="priority-actions" data-pk="{0}" data-priority="{1}">'
            '  <button type="button" class="button" {2} data-action="decrement" title="Move up">'  # noqa: E501
            '    <span class="visually-hidden">'
            "      Move up"
            "    </span>"
            "  </button>"
            '  <button type="button" class="button" {2} data-action="increment" title="Move down">'  # noqa: E501
            '    <span class="visually-hidden">'
            "      Move down"
            "    </span>"
            "  </button>"
            "</div>",
            obj.pk,
            obj.priority,
            boolean_attrs,
        )

    def get_urls(self):
        urls = [
            path(
                "taxon_options",
                self.admin_site.admin_view(self.taxon_options_json_view),
                name="%s_%s_taxon_options"
                % (self.model._meta.app_label, self.model._meta.model_name),
            ),
            path(
                "<int:taxon_id>/update_priority_list",
                self.admin_site.admin_view(self.update_priority_list_json_view),
                name="%s_%s_update_priority_list"
                % (self.model._meta.app_label, self.model._meta.model_name),
            ),
        ]
        return urls + super().get_urls()

    def get_update_priority_list_url(self, taxon_id):
        return reverse(
            "%s:%s_%s_update_priority_list"
            % (
                self.admin_site.name,
                self.model._meta.app_label,
                self.model._meta.model_name,
            ),
            args=[taxon_id],
        )

    @method_decorator(require_POST, csrf_protect)
    def update_priority_list_json_view(self, request, taxon_id):
        if not self.has_change_permission(request):
            raise PermissionDenied

        try:
            posted_data = json.loads(request.body)
            if not (
                type(posted_data) is list and all(type(v) is int for v in posted_data)
            ):
                raise InvalidPriorityListJson
        except (json.JSONDecodeError, InvalidPriorityListJson):
            return JsonResponse(
                {
                    "error": (
                        "Request body MUST only contain valid "
                        "JSON in the form of a list with integers."
                    )
                },
                status=400,
            )

        queryset = self.get_queryset(request).filter(
            taxon_id=taxon_id, pk__in=posted_data
        )

        priority_slots = tuple([obj.priority for obj in queryset.order_by("priority")])

        objects_to_update = []

        for object_to_update in queryset:
            object_to_update.priority = priority_slots[
                posted_data.index(object_to_update.pk)
            ]
            objects_to_update.append(object_to_update)

        queryset.bulk_update(objects_to_update, fields=["priority"])

        return JsonResponse(
            {
                "results": [
                    {"id": obj.pk, "priority": obj.priority}
                    for obj in queryset.order_by("priority")
                ]
            }
        )

    def taxon_options_json_view(self, request):
        term = request.GET.get("term", "")

        queryset = self.model.taxon.get_queryset()

        if len(term) == 0:
            queryset = queryset.all()
        else:
            queryset = queryset.filter(scientific_name__icontains=term)

        paginator = Paginator(queryset, 50)
        page = paginator.get_page(request.GET.get("page", 1))

        return JsonResponse(
            {
                "results": [{"id": str(obj.id), "text": str(obj)} for obj in page],
                "pagination": {"more": page.has_next()},
            }
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        db = kwargs.get("using")

        if db_field.name == "taxon":
            kwargs["widget"] = TaxonSelect(
                db_field, self.admin_site, self.model, using=db
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.has_perm("media.manage_others"):
            return qs
        return qs.filter(created_by=request.user)

    def get_ordering(self, request):
        is_filtered_by_taxon = self.get_taxon_filter_value(request.GET) is not None
        return ("priority",) if is_filtered_by_taxon else ("-created_at",)

    def get_changelist_instance(self, request):
        cl = super().get_changelist_instance(request)

        primary_ordering_field, *_ = cl.get_ordering(request, cl.get_queryset(request))
        _, _, primary_ordering_field_name = primary_ordering_field.rpartition("-")

        is_ordered_by_priority = primary_ordering_field_name == "priority"

        is_filtered_by_taxon = (
            self.get_taxon_filter_value(cl.get_filters_params()) is not None
        )

        self.enable_priority_sorting = is_ordered_by_priority and is_filtered_by_taxon

        # annotate for usage in templates etc.
        cl.enable_priority_sorting = self.enable_priority_sorting

        return cl

    def save_model(self, request, obj, form, change):
        if not hasattr(obj, "created_by"):
            obj.created_by = request.user

        if change:
            obj.updated_at = timezone.now()

        super().save_model(request, obj, form, change)

        if hasattr(obj, "create_renditions") and callable(obj.create_renditions):
            obj.create_renditions()

    def add_view(self, request, form_url="", extra_context=False):
        extra_context = self._extra_context_with_defaults(extra_context)
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=False):
        extra_context = self._extra_context_with_defaults(extra_context)
        return super().change_view(request, object_id, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        filtered_by_taxon_id = self.get_taxon_filter_value(request.GET)

        if filtered_by_taxon_id is not None:
            extra_context["update_priority_list_url"] = self.get_update_priority_list_url(
                filtered_by_taxon_id
            )

        return super().changelist_view(request, extra_context)

    def _extra_context_with_defaults(self, extra_context):
        return {
            "show_save_and_continue": False,
            "show_save_and_add_another": True,
            **(extra_context or {}),
        }

    @classmethod
    def get_taxon_filter_value(cls, parameters):
        return TaxonListFilter.normalize_value(
            parameters.get(TaxonListFilter.parameter_name)
        )

    def change_taxon_action(self, request, queryset):
        """
        Admin action to change taxon for multiple selected images
        """
        if "apply" in request.POST:
            new_taxon_id = request.POST.get("new_taxon")

            if new_taxon_id:
                try:
                    new_taxon = Taxon.objects.get(pk=new_taxon_id)

                    # Find the next available priority for the new taxon
                    from media.models import available_priorities

                    # Use a transaction to ensure atomicity
                    with transaction.atomic():
                        # Get the next available priorities for the new taxon
                        priority_generator = available_priorities(new_taxon)

                        # Update each image individually with a new priority
                        count = 0
                        for img in queryset:
                            img.taxon = new_taxon
                            img.priority = next(priority_generator)
                            img.save(update_fields=["taxon", "priority"])
                            count += 1

                    message = (
                        f"Successfully moved {count} images to taxon: "
                        f"{new_taxon.scientific_name}"
                    )

                    self.message_user(request, message)
                    return None

                except Taxon.DoesNotExist:
                    self.message_user(
                        request, "Selected taxon does not exist.", level=messages.ERROR
                    )
            else:
                self.message_user(request, "No taxon selected.", level=messages.ERROR)

        # Create a temporary field to get the widget
        taxon_field = self.model._meta.get_field("taxon")
        form_field = self.formfield_for_foreignkey(taxon_field, request)

        class TaxonChangeForm(forms.Form):
            _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
            new_taxon = form_field

        form = TaxonChangeForm(
            initial={
                "_selected_action": request.POST.getlist(
                    admin.helpers.ACTION_CHECKBOX_NAME
                )
            }
        )

        changelist_url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist"
        )

        context = {
            "queryset": queryset,
            "form": form,
            "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
            "opts": self.model._meta,
            "cancel_url": changelist_url,
        }

        return render(
            request,
            "admin/media/change_taxon_intermediate.html",
            context,
        )

    change_taxon_action.short_description = "Change taxon for selected images"


class ImageAdmin(MediaAdmin):
    form = ImageForm
    actions: ClassVar[list[str]] = ["change_taxon_action"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Include images that are not marked as ImageLabeling
        return qs.filter(
            Q(attributes__imagelabeling__isnull=True) | Q(attributes__imagelabeling=False)
        )

    def get_preview_html(self, obj):
        small_rendition = obj.renditions.get("s")

        if small_rendition:
            return format_html("<img src={} />", small_rendition["url"])

        return super().get_preview_html(obj)


class ImageLabelingAdmin(MediaAdmin):
    form = ImageLabelingImageForm
    list_filter = (TaxonListFilter,)
    actions: ClassVar[list[str]] = ["change_taxon_action"]

    def get_preview_html(self, obj):
        """Display preview thumbnail in changelist"""
        small_rendition = obj.renditions.get("s")
        if small_rendition:
            return format_html("<img src={} />", small_rendition["url"])
        return super().get_preview_html(obj)

    def get_form(self, request, obj=None, change=False, **kwargs):
        """
        Return the form class directly and manually apply widgets.
        """
        # Get the form class
        FormClass = self.form

        # Manually override the taxon field widget
        db_field = self.model._meta.get_field("taxon")

        # Create a new form class that inherits from our form
        # and override just the taxon field
        class ModifiedForm(FormClass):
            pass

        # Apply the TaxonSelect widget to the taxon field
        ModifiedForm.base_fields = FormClass.base_fields.copy()
        ModifiedForm.base_fields["taxon"] = self.formfield_for_foreignkey(
            db_field, request
        )

        return ModifiedForm

    def get_fieldsets(self, request, obj=None):
        """
        Generate fieldsets from the actual form instance fields.
        """
        form_instance = self.form()
        field_names = list(form_instance.fields.keys())

        return [
            (None, {"fields": field_names}),
        ]

    def save_model(self, request, obj, form, change):
        """Handle both single image and ZIP file uploads"""
        uploaded_file = request.FILES.get("file")

        if uploaded_file and uploaded_file.name.lower().endswith(".zip"):
            # Handle ZIP upload
            self._process_zip_upload(request, obj, uploaded_file)
        else:
            # Handle normal single image upload
            if not hasattr(obj, "created_by"):
                obj.created_by = request.user

            if change:
                obj.updated_at = timezone.now()

            super().save_model(request, obj, form, change)

            if hasattr(obj, "create_renditions") and callable(obj.create_renditions):
                obj.create_renditions()

    def _process_zip_upload(self, request, template_obj, zip_file):
        """Extract ZIP and create multiple images"""
        import os
        import zipfile
        from io import BytesIO

        from django.core.files.uploadedfile import InMemoryUploadedFile
        from django.utils.text import slugify

        try:
            # Get the ZIP filename at the start
            zip_filename = getattr(zip_file, "name", "ZIP archive")

            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                # Get image files
                image_files = [
                    f
                    for f in zip_ref.namelist()
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff"))
                    and not f.startswith("__MACOSX")
                    and not f.startswith(".")
                    and not os.path.basename(f).startswith(".")
                ]

                if not image_files:
                    messages.error(request, "No valid image files found in ZIP")
                    return

                created_count = 0
                failed_count = 0
                taxon = template_obj.taxon

                if not taxon:
                    messages.error(request, "Taxon is required for ZIP upload")
                    return

                # Title stays the same for all images
                title = template_obj.attributes.get("title", taxon.scientific_name)

                # Get metadata from the form (shared across all images)
                shared_metadata = template_obj.attributes.copy()

                # Find the next available number for this taxon
                from media.models import Image as BaseImage

                existing_images = BaseImage.objects.filter(
                    slug__startswith=f"{taxon.slug}-"
                ).order_by("-slug")

                # Extract numbers from existing slugs to find the highest
                start_idx = 1
                if existing_images.exists():
                    for img in existing_images:
                        slug_parts = img.slug.split("-")
                        if slug_parts[-1].isdigit():
                            start_idx = max(start_idx, int(slug_parts[-1]) + 1)

                for idx, filename in enumerate(sorted(image_files), start=start_idx):
                    try:
                        # Read image data
                        image_data = zip_ref.read(filename)
                        file_obj = BytesIO(image_data)

                        # Create slug with running number (for uniqueness)
                        slug = slugify(f"{taxon.slug}-{idx}")

                        # Double-check uniqueness
                        counter = 1
                        original_slug = slug
                        while BaseImage.objects.filter(slug=slug).exists():
                            slug = f"{original_slug}-{counter}"
                            counter += 1

                        # Get file extension
                        _, ext = os.path.splitext(filename)
                        ext = ext.lower()

                        # Determine content type
                        content_type_map = {
                            ".png": "image/png",
                            ".jpg": "image/jpeg",
                            ".jpeg": "image/jpeg",
                            ".tif": "image/tiff",
                            ".tiff": "image/tiff",
                        }
                        content_type = content_type_map.get(ext, "image/jpeg")

                        # Use atomic transaction for each image
                        with transaction.atomic():
                            # Create new Image object with shared metadata
                            # Title stays the same (no number), only slug has number
                            img = ImageLabelingImage(
                                slug=slug,
                                taxon=taxon,
                                type=content_type,
                                attributes={
                                    **shared_metadata,
                                    "title": title,
                                },  # title without number
                                created_by=request.user,
                                created_at=timezone.now(),
                            )

                            # Save file (filename gets the number from slug)
                            img.file.save(
                                f"{slug}{ext}",
                                InMemoryUploadedFile(
                                    file_obj,
                                    None,
                                    f"{slug}{ext}",
                                    content_type,
                                    len(image_data),
                                    None,
                                ),
                                save=True,
                            )

                            # Create renditions
                            if hasattr(img, "create_renditions"):
                                img.create_renditions()

                            created_count += 1

                    except Exception as e:
                        failed_count += 1
                        print(f"Error processing {filename}: {e!s}")
                        import traceback

                        traceback.print_exc()

                if created_count > 0:
                    messages.success(
                        request,
                        f"Successfully created {created_count} images "
                        f"from {zip_filename}",
                    )
                if failed_count > 0:
                    messages.warning(
                        request,
                        f"Failed to create {failed_count} images. "
                        "Check server logs for details.",
                    )

        except zipfile.BadZipFile:
            messages.error(request, "Invalid ZIP file")
        except Exception as e:
            messages.error(request, f"Error processing ZIP: {e!s}")
            import traceback

            print(traceback.format_exc())

    def response_add(self, request, obj, post_url_continue=None):
        """
        Override to handle ZIP uploads and 'Save and add another' button
        """
        uploaded_file = request.FILES.get("file")
        if uploaded_file and uploaded_file.name.lower().endswith(".zip"):
            # Check if "Save and add another" was clicked
            if "_addanother" in request.POST:
                # Redirect back to add form
                return redirect("admin:media_imagelabelingimage_add")
            else:
                # For regular save, redirect to changelist
                return redirect("admin:media_imagelabelingimage_changelist")
        return super().response_add(request, obj, post_url_continue)


admin.site.register(Image, ImageAdmin)
admin.site.register(ImageLabelingImage, ImageLabelingAdmin)
