from typing import ClassVar

from django import forms
from django.conf import settings


class ImageFileInput(forms.widgets.ClearableFileInput):
    pass


class Tag(forms.widgets.SelectMultiple):
    class Media:
        extra_suffix = "" if settings.DEBUG else ".min"
        js = (
            "admin/js/vendor/jquery/jquery%s.js" % extra_suffix,
            "admin/js/vendor/select2/select2.full%s.js" % extra_suffix,
            "admin/js/jquery.init.js",
            "admin/js/mediatag.js",
        )
        css: ClassVar[dict] = {
            "screen": (
                "admin/css/vendor/select2/select2%s.css" % extra_suffix,
                "admin/css/autocomplete.css",
            )
        }

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs=extra_attrs)

        attrs.update(
            {
                "class": ("%s media-tag-widget" % attrs.get("class", "")).strip(),
                "data-tags": "true",
                "data-theme": "admin-autocomplete",
            }
        )

        return attrs
