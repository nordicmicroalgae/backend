from django.db.models import Count, F

from core.views.generics import CollectionView, ClientError
from media.models import Media, Image


class MediaCollectionView(CollectionView):

    fields = (
        'slug',
        'file',
        'type',
        'created_at',
        'updated_at',
        'attributes',
        'renditions',
    )

    model_types = {
        'all': Media,
        'image': Image,
    }

    plural_key = 'media'

    def get_queryset(self, *args, **kwargs):
        model_type = self.request.GET.get('type', 'all')

        try:
            model = self.model_types[model_type]
        except KeyError:
            raise ClientError('Unknown value provided for type.')

        queryset = model.objects.all()


        artist = self.request.GET.get('artist')

        if artist != None:
            queryset = queryset.filter(
                attributes__contains={
                    'photographer_artist': artist
                }
            )

        gallery = self.request.GET.get('gallery')

        if gallery != None:
            queryset = queryset.filter(
                attributes__contains={
                    'galleries': [gallery]
                }
            )

        taxon = self.request.GET.get('taxon')

        if taxon != None:
            queryset = queryset.filter(taxon__slug=taxon)


        queryset = queryset.order_by(
            'priority' if taxon else '-created_at'
        )


        return queryset


class ArtistCollectionView(CollectionView):
    queryset = Media.objects

    fields = (
        'artist',
        'number_of_contributions',
    )

    plural_key = 'artists'

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.values(
            artist=F('attributes__photographer_artist')
        )

        queryset = queryset.annotate(
            number_of_contributions=Count(
                'attributes__photographer_artist'
            )
        )

        queryset = queryset.order_by('-number_of_contributions')

        return queryset
