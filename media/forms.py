import os
import yaml

from django import forms
from django.conf import settings


def get_fields_config(media_type):
    config_path = os.path.join(
        settings.BASE_DIR, 'media', 'config', 'fields.yaml'
    )

    config = {}
    with open(config_path, 'r', encoding='utf8') as infile:
        config = yaml.safe_load(infile)

    return config[media_type]


def configure_form(form_cls, form_config):
    declared_fields = {}

    for field_config in form_config:
        field_cls = getattr(forms, field_config.get('type', 'CharField'))

        field_kwargs = {}

        if 'widget' in field_config:
            field_kwargs['widget'] = getattr(
                forms.widgets,
                field_config['widget']
            )

        if 'label' in field_config:
            field_kwargs['label'] = str(field_config['label'])

        if 'help_text' in field_config:
            field_kwargs['help_text'] = str(field_config['help_text'])

        if 'required' in field_config:
            field_kwargs['required'] = bool(field_config['required'])

        if 'choices' in field_config:
            field_kwargs['choices'] = [
                (choice, choice) for choice in field_config['choices']
            ]

        if 'initial' in field_config:
            field_kwargs['initial'] = field_config['initial']


        is_select_widget = (
            field_cls == forms.ChoiceField and
            field_kwargs.get('widget', None) in [forms.widgets.Select, None]
        )

        if is_select_widget:
            field_kwargs['choices'] = (
                [(None, '---------')] + field_kwargs.get('choices', [])
            )

        declared_fields[field_config['key']] = field_cls(**field_kwargs)

    form_cls.declared_fields.update(declared_fields)
    form_cls.configured_fields = form_config


class MediaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)

        if instance:
            kwargs.setdefault('initial', {})
            kwargs['initial'].update(**instance.attributes)

        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        if hasattr(self, 'configured_fields'):
            for configured_field in self.configured_fields:
                field_key = configured_field['key']
                if field_key in self.cleaned_data.keys():
                    field_value = self.cleaned_data[field_key]
                    self.instance.attributes[field_key] = field_value

        return super().save(*args, **kwargs)


class ImageForm(MediaForm):
    pass

configure_form(ImageForm, get_fields_config('image'))