def get_media_models(include_base=False):
    from .models import Media

    subclasses = Media.__subclasses__()
    return [Media] + subclasses if include_base else subclasses
