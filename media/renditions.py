import base64
import os
from io import BytesIO
from typing import ClassVar

from PIL import Image as PillowImage
from PIL import ImageDraw, ImageFilter, ImageFont

from media.storage import default_rendition_storage


class Rendition:
    storage = default_rendition_storage

    def __init__(self, label, instance, *options):
        self.label = label
        self.instance = instance
        self.options = options

    def create(self):
        self.storage.delete(self.relative_path)

        self.source.seek(0)

        with BytesIO(self.source.read()) as input_buffer:
            output_buffer = self.render(input_buffer)
            self.save(output_buffer)
            output_buffer.close()

    def save(self, output_buffer):
        self.storage.save(self.relative_path, output_buffer)

    def delete(self):
        self.storage.delete(self.relative_path)

    def render(self, input_buffer):
        raise NotImplementedError("Subclasses must implement render() method.")

    def to_dict(self):
        return {"url": self.url, "type": self.type}

    @property
    def source(self):
        return self.instance.file

    @property
    def path(self):
        return self.storage.path(self.relative_path)

    @property
    def relative_path(self):
        return os.path.join(self.label, self.name)

    @property
    def name(self):
        return self.source.name

    @property
    def type(self):
        return self.instance.type

    @property
    def url(self):
        return self.storage.url(self.relative_path)


def _apply_watermark(image, text):
    """Overlay semi-transparent watermark text in the bottom-right corner."""
    original_mode = image.mode
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    overlay = PillowImage.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_size = max(12, int(image.height * 0.025))
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", font_size)
    except (OSError, IOError):
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    padding = int(font_size * 0.8)
    x = image.width - text_width - padding
    y = image.height - text_height - padding

    shadow_color = (0, 0, 0, 128)
    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        draw.text((x + dx, y + dy), text, font=font, fill=shadow_color)

    draw.text((x, y), text, font=font, fill=(255, 255, 255, 180))

    image = PillowImage.alpha_composite(image, overlay)

    if original_mode != "RGBA":
        image = image.convert(original_mode)

    return image


class Image(Rendition):
    format = "webp"

    def render(self, input_buffer):
        output_buffer = BytesIO()

        with PillowImage.open(input_buffer) as image:
            processed_image = self.process(image)
            processed_image.save(output_buffer, format=self.format)

        return output_buffer

    def process(self, image):
        copyright_stamp = self.instance.attributes.get("copyright_stamp", "")
        if copyright_stamp:
            image = _apply_watermark(image, copyright_stamp)
        return image

    @property
    def name(self):
        root, _ = os.path.splitext(self.source.name)
        return "%s.%s" % (root, self.format)

    @property
    def type(self):
        return "image/%s" % self.format


class ResizedImage(Image):
    def process(self, image):
        image = super().process(image)

        orig_width, orig_height = image.size

        max_width, max_height = self.options

        factor = min(max_width / orig_width, max_height / orig_height)

        if factor >= 1:
            return image

        resized_image = image.resize(
            (int(orig_width * factor), int(orig_height * factor)), PillowImage.LANCZOS
        )

        return resized_image


class EmbededPreviewImage(Image):
    def process(self, image):
        image = super().process(image)

        preview_image = image.convert("RGB")

        preview_image.thumbnail((80, 80))

        preview_image = preview_image.filter(ImageFilter.GaussianBlur(radius=4))

        return preview_image

    def save(self, output_buffer):
        self.encoded_preview = base64.b64encode(output_buffer.getvalue())

    def delete(self):
        self.encoded_preview = None

    @property
    def url(self):
        return "data:image/webp;base64,%s" % self.encoded_preview.decode("ascii")


class Specification:
    def __init__(self, label, rendition, *options):
        if not issubclass(rendition, Rendition):
            raise ValueError("rendition must be subclass of Rendition")

        self.label = label
        self.rendition = rendition
        self.options = options

    def to_rendition(self, instance):
        return self.rendition(self.label, instance, *self.options)

    _registry: ClassVar[dict] = {}

    @classmethod
    def register(cls, model, **specs):
        cls._registry[model] = [cls(label, *spec) for label, spec in specs.items()]

    @classmethod
    def get(cls, model):
        """
        Return the specification list for the given model.

        Lookup order:
        1. Exact match in the registry.
        2. Any registered model that is a base class of the provided model
           (i.e. issubclass(model, registered_model)).
        3. None if nothing found.

        This makes proxy models and subclasses inherit the renditions
        configuration from their parent model (e.g. IFCBImage -> Image).
        """
        # 1) exact match first
        spec = cls._registry.get(model)
        if spec is not None:
            return spec

        # 2) fallback: find first registered model that is a base class
        for registered_model, registered_spec in cls._registry.items():
            try:
                if issubclass(model, registered_model):
                    return registered_spec
            except TypeError:
                # issubclass can raise if `model` is not a class; skip in that case
                continue

        # 3) nothing found
        return None

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

        if not specification:
            # No renditions specification found for this model or its bases.
            # This can happen for unregistered models or if registration occurred
            # before/after import ordering that prevented a match.
            # Log/raise an informative exception instead of failing with TypeError.
            raise RuntimeError(
                f"No renditions Specification registered for model "
                f"{self.__class__.__name__}. "
                "Ensure that a renditions.Specification is registered "
                "for this model or one of its base classes (e.g. Image), "
                "and that import order is correct."
            )

        for entry in specification:
            rendition = entry.to_rendition(self)
            rendition.create()
            self.renditions[rendition.label] = rendition.to_dict()

        self.save(update_fields=["renditions"])

    def delete_renditions(self):
        specification = Specification.get(self.__class__)

        for entry in specification:
            rendition = entry.to_rendition(self)
            rendition.delete()

        self.renditions = {}
        self.save(update_fields=["renditions"])
