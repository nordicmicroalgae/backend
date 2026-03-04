import os
from typing import ClassVar

import yaml
from django import forms
from django.conf import settings

from media import widgets
from media.models import Image, ImageLabelingImage, Media


class ImageUploadField(forms.ImageField):
    widget = widgets.ImageFileInput


class ImageOrZipUploadField(forms.FileField):
    """Field that accepts both images and ZIP archives"""

    widget = widgets.ImageFileInput

    # Upload limit configuration
    MAX_IMAGES_IN_ZIP = 100
    MAX_ZIP_SIZE_MB = 50

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "help_text",
            (
                f"Upload a single image (PNG, JPG, TIF) or a ZIP archive "
                f"containing multiple images (max {self.MAX_IMAGES_IN_ZIP} images, "
                f"max {self.MAX_ZIP_SIZE_MB}MB). "
                f"All images from a ZIP will share the same metadata."
            ),
        )
        super().__init__(*args, **kwargs)

    def to_python(self, data):
        """
        Override to allow ZIP files in addition to images.
        For ZIP files, validate size and image count.
        """
        if data is None:
            return None

        if hasattr(data, "name") and data.name.lower().endswith(".zip"):
            # Validate ZIP file size
            if data.size > self.MAX_ZIP_SIZE_MB * 1024 * 1024:
                raise forms.ValidationError(
                    f"ZIP file is too large. Maximum size is {self.MAX_ZIP_SIZE_MB}MB."
                )

            # Validate number of images in ZIP
            import zipfile

            try:
                with zipfile.ZipFile(data, "r") as zip_ref:
                    image_files = [
                        f
                        for f in zip_ref.namelist()
                        if f.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff"))
                        and not f.startswith("__MACOSX")
                        and not f.startswith(".")
                        and not os.path.basename(f).startswith(".")
                    ]

                    if len(image_files) == 0:
                        raise forms.ValidationError(
                            "ZIP archive contains no valid image files."
                        )

                    if len(image_files) > self.MAX_IMAGES_IN_ZIP:
                        raise forms.ValidationError(
                            f"ZIP archive contains {len(image_files)} images. "
                            f"Maximum allowed is {self.MAX_IMAGES_IN_ZIP}."
                        )

                # Reset file pointer after reading
                data.seek(0)

            except zipfile.BadZipFile:
                raise forms.ValidationError("Invalid ZIP file.")

            return data

        # For image files, use the parent FileField validation
        return forms.FileField.to_python(self, data)


class TagField(forms.MultipleChoiceField):
    widget = widgets.Tag

    def valid_value(self, value):
        return isinstance(value, str)


FORM_FIELDS = {
    "TagField": TagField,
}


def get_field_class(field_type):
    if field_type in FORM_FIELDS:
        return FORM_FIELDS[field_type]
    return getattr(forms, field_type)


def get_fields_config(media_type):
    config_path = os.path.join(settings.BASE_DIR, "media", "config", "fields.yaml")

    config = {}
    with open(config_path, "r", encoding="utf8") as infile:
        config = yaml.safe_load(infile)

    return config.get(media_type, [])


def tagchoices_factory(model, tagset, choices=[]):
    def get_choices():
        # Special handling for 'institute' - it's not in Tag.tagsets
        if tagset == "institute":
            # Get all unique institutes from imagelabeling images
            institutes = set()
            for img in model.objects.filter(attributes__imagelabeling=True):
                institute = img.attributes.get("institute")
                if isinstance(institute, list):
                    institutes.update(inst for inst in institute if inst)
                elif isinstance(institute, str) and institute:
                    institutes.add(institute)

            # Combine suggestions and database values, remove duplicates
            all_institutes = set(choice[0] for choice in choices) | institutes
            return sorted([(inst, inst) for inst in all_institutes])

        # Regular tagsets use the Tag class
        qs = model.objects.get_tagset(tagset)
        return set(choices + [(tag["name"], tag["name"]) for tag in qs])

    return get_choices


def configure_form(form_cls, form_config):
    declared_fields = {}

    for field_config in form_config:
        field_cls = get_field_class(field_config.get("type", "CharField"))

        field_kwargs = {}

        if "widget" in field_config:
            field_kwargs["widget"] = getattr(forms.widgets, field_config["widget"])

        if "label" in field_config:
            field_kwargs["label"] = str(field_config["label"])

        if "help_text" in field_config:
            field_kwargs["help_text"] = str(field_config["help_text"])

        if "required" in field_config:
            field_kwargs["required"] = bool(field_config["required"])

        if "choices" in field_config:
            field_kwargs["choices"] = [
                tuple(choice) if isinstance(choice, list) else (choice, choice)
                for choice in field_config["choices"]
            ]

        if "initial" in field_config:
            field_kwargs["initial"] = field_config["initial"]

        is_tag_widget = field_cls == TagField

        if is_tag_widget:
            field_kwargs["choices"] = tagchoices_factory(
                getattr(form_cls.Meta, "model"),
                field_config["key"],
                choices=[
                    (choice, choice) for choice in field_config.get("suggestions", [])
                ],
            )

        is_select_widget = field_cls == forms.ChoiceField and field_kwargs.get(
            "widget", None
        ) in [forms.widgets.Select, None]

        if is_select_widget:
            field_kwargs["choices"] = [
                (None, "---------"),
                *field_kwargs.get("choices", []),
            ]

        declared_fields[field_config["key"]] = field_cls(**field_kwargs)

    form_cls.declared_fields.update(declared_fields)
    form_cls.configured_fields = form_config


def add_configured_fields_to_form(form_instance, form_config, model_class):
    """
    Add configured fields to a form instance at runtime.
    Used by ImageLabelingImageForm to avoid inheriting fields from ImageForm.
    """
    for field_config in form_config:
        field_cls = get_field_class(field_config.get("type", "CharField"))

        field_kwargs = {}

        if "widget" in field_config:
            field_kwargs["widget"] = getattr(forms.widgets, field_config["widget"])

        if "label" in field_config:
            field_kwargs["label"] = str(field_config["label"])

        if "help_text" in field_config:
            field_kwargs["help_text"] = str(field_config["help_text"])

        if "required" in field_config:
            field_kwargs["required"] = bool(field_config["required"])

        if "choices" in field_config:
            field_kwargs["choices"] = [
                tuple(choice) if isinstance(choice, list) else (choice, choice)
                for choice in field_config["choices"]
            ]

        if "initial" in field_config:
            field_kwargs["initial"] = field_config["initial"]

        is_tag_widget = field_cls == TagField

        if is_tag_widget:
            field_kwargs["choices"] = tagchoices_factory(
                model_class,
                field_config["key"],
                choices=[
                    (choice, choice) for choice in field_config.get("suggestions", [])
                ],
            )

        is_select_widget = field_cls == forms.ChoiceField and field_kwargs.get(
            "widget", None
        ) in [forms.widgets.Select, None]

        if is_select_widget:
            field_kwargs["choices"] = [
                (None, "---------"),
                *field_kwargs.get("choices", []),
            ]

        form_instance.fields[field_config["key"]] = field_cls(**field_kwargs)


class MediaForm(forms.ModelForm):
    class Meta:
        fields = ("taxon", "file")

        model = Media

    class Media:
        css: ClassVar[dict] = {"screen": ("admin/css/media_form.css",)}
        js = (
            "admin/js/jquery.init.js",
            "admin/js/MediaFormEnhancements.js",
        )

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance", None)

        if instance:
            kwargs.setdefault("initial", {})
            kwargs["initial"].update(**instance.attributes)

        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        # TODO: Implement better solution for determining content_type.
        #
        # Do not rely on values provided by the client, which is the case
        # for content_type for uploaded files. At least the value needs to
        # be verified.
        #
        # This is fine for now since ImageField is the only one being used
        # at the moment and in that case the value for content_type is
        # derived from the image type received by Pillow upon validation.
        if "file" in self.changed_data:
            self.instance.type = self.cleaned_data["file"].content_type

        if hasattr(self, "configured_fields"):
            for configured_field in self.configured_fields:
                field_key = configured_field["key"]
                if field_key in self.cleaned_data.keys():
                    field_value = self.cleaned_data[field_key]
                    self.instance.attributes[field_key] = field_value

        return super().save(*args, **kwargs)


class ImageForm(MediaForm):
    class Meta(MediaForm.Meta):
        model = Image

    file = ImageUploadField()


class ImageLabelingImageForm(forms.ModelForm):
    """
    Form for ImageLabeling images with ZIP upload support.
    """

    class Meta:
        model = ImageLabelingImage
        fields = ("taxon", "file")

    class Media:
        css: ClassVar[dict[str, tuple[str, ...]]] = {
            "screen": ("admin/css/media_form.css",)
        }
        js: ClassVar[tuple[str, ...]] = (
            "admin/js/jquery.init.js",
            "admin/js/MediaFormEnhancements.js",
        )

    # Override file field to accept both images and ZIP archives
    file = ImageOrZipUploadField(label="Image file or ZIP archive")

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance", None)

        if instance:
            kwargs.setdefault("initial", {})
            kwargs["initial"].update(**instance.attributes)

        super().__init__(*args, **kwargs)

        imagelabeling_config = get_fields_config("imagelabeling")
        add_configured_fields_to_form(self, imagelabeling_config, ImageLabelingImage)

        # Store the config for use in save()
        self.configured_fields = imagelabeling_config

    def save(self, *args, **kwargs):
        # Handle content type for file uploads
        if "file" in self.changed_data:
            self.instance.type = self.cleaned_data["file"].content_type

        # Save configured fields to attributes
        if hasattr(self, "configured_fields"):
            for configured_field in self.configured_fields:
                field_key = configured_field["key"]
                if field_key in self.cleaned_data.keys():
                    field_value = self.cleaned_data[field_key]
                    self.instance.attributes[field_key] = field_value

        # Mark as imagelabeling
        self.instance.attributes = dict(self.instance.attributes or {})
        self.instance.attributes["imagelabeling"] = True

        return super().save(*args, **kwargs)


configure_form(ImageForm, get_fields_config("image"))
