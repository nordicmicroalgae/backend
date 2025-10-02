import os
from typing import ClassVar

import yaml
from django import forms
from django.conf import settings

from media import widgets
from media.models import Image, Media


class ImageUploadField(forms.ImageField):
    widget = widgets.ImageFileInput


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

    return config[media_type]


def tagchoices_factory(model, tagset, choices=[]):
    def get_choices():
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
                (choice, choice) for choice in field_config["choices"]
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


configure_form(ImageForm, get_fields_config("image"))
