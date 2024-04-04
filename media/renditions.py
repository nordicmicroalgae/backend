import os
import base64
from io import BytesIO
from PIL import Image as PillowImage, ImageFilter

from media.storage import default_rendition_storage


class Rendition:

    storage = default_rendition_storage

    def __init__(self, label, instance, *options):
        self.label = label
        self.instance = instance
        self.options = options

    def create(self):
        self.storage.delete(self.path)

        self.source.seek(0)

        with BytesIO(self.source.read()) as input_buffer:
            output_buffer = self.render(input_buffer)
            self.save(output_buffer)
            output_buffer.close()

    def save(self, output_buffer):
        self.storage.save(self.path, output_buffer)

    def delete(self):
        self.storage.delete(self.path)

    def render(self, input_buffer):
        raise NotImplementedError(
            'Subclasses must implement render() method.'
        )

    def to_dict(self):
        return {'url': self.url, 'type': self.type}

    @property
    def source(self):
        return self.instance.file

    @property
    def path(self):
        return self.storage.path(
            os.path.join(self.label, self.name)
        )

    @property
    def name(self):
        return self.source.name

    @property
    def type(self):
        return self.instance.type

    @property
    def url(self):
        return self.storage.url(
            os.path.join(self.label, self.name)
        )

class Image(Rendition):

    format = 'webp'

    def render(self, input_buffer):
        output_buffer = BytesIO()

        with PillowImage.open(input_buffer) as image:
            processed_image = self.process(image)
            processed_image.save(output_buffer, format=self.format)

        return output_buffer

    def process(self, image):
        return image

    @property
    def name(self):
        root, _ = os.path.splitext(self.source.name)
        return '%s.%s' % (root, self.format)

    @property
    def type(self):
        return 'image/%s' % self.format

class ResizedImage(Image):

    def process(self, image):
        image = super().process(image)

        orig_width, orig_height = image.size

        max_width, max_height = self.options

        factor = min(max_width/orig_width, max_height/orig_height)

        if factor >= 1:
            return image

        resized_image = image.resize((
            int(orig_width*factor),
            int(orig_height*factor)),
            PillowImage.LANCZOS
        )

        return resized_image

class EmbededPreviewImage(Image):

    def process(self, image):
        image = super().process(image)

        preview_image = image.convert('RGB')

        preview_image.thumbnail((80, 80))

        preview_image = preview_image.filter(
            ImageFilter.GaussianBlur(radius=4)
        )

        return preview_image

    def save(self, output_buffer):
        self.encoded_preview = base64.b64encode(
            output_buffer.getvalue()
        )

    def delete(self):
        self.encoded_preview = None

    @property
    def url(self):
        return (
            'data:image/webp;base64,%s'
            % self.encoded_preview.decode('ascii')
        )


class Specification:

    def __init__(self, label, rendition, *options):
        if not issubclass(rendition, Rendition):
            raise ValueError(
                'rendition must be subclass of Rendition'
            )

        self.label = label
        self.rendition = rendition
        self.options = options

    def to_rendition(self, instance):
        return self.rendition(self.label, instance, *self.options)


    _registry = {}

    @classmethod
    def register(cls, model, **specs):
        cls._registry[model] = [
            cls(label, *spec)
            for label, spec in specs.items()
        ]

    @classmethod
    def get(cls, model):
        return cls._registry.get(model)

    @classmethod
    def get_registered_models(cls):
        return list(cls._registry.keys())


def register(**specs):
    def _register_model_spec_wrapper(model):
        Specification.register(model, **specs)
        return model
    return _register_model_spec_wrapper

def get_registered_models():
    return Specification.get_registered_models()


class ModelActionsMixin:

    def create_renditions(self):
        self.renditions = {}
        specification = Specification.get(self.__class__)

        for entry in specification:
            rendition = entry.to_rendition(self)
            rendition.create()
            self.renditions[rendition.label] = rendition.to_dict()

        self.save(update_fields=['renditions'])

    def delete_renditions(self):
        specification = Specification.get(self.__class__)

        for entry in specification:
            rendition = entry.to_rendition(self)
            rendition.delete()

        self.renditions = {}
        self.save(update_fields=['renditions'])
