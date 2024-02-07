import os
from io import BytesIO

from PIL import Image as PillowImage

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
            self.storage.save(self.path, output_buffer)
            output_buffer.close()

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

    def render(self, input_buffer):
        output_buffer = BytesIO()

        with PillowImage.open(input_buffer) as image:
            processed_image = self.process(image)
            processed_image.save(output_buffer, format=image.format)

        return output_buffer

    def process(self, image):
        return image

class ResizedImage(Image):

    def process(self, image):
        orig_width, orig_height = image.size

        max_width, max_height = self.options

        factor = min(max_width/orig_width, max_height/orig_height)

        resized_image = image.resize((
            int(orig_width*factor),
            int(orig_height*factor)),
            PillowImage.LANCZOS
        )

        return resized_image


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
