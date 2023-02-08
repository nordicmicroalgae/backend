from django.db.models import Count, F
from django.http import JsonResponse
from django.views import View

from media.models import Media, Image

class MediaCollectionView(View):

    model_types = {
        'all': Media,
        'image': Image,
    }

    fieldnames = [
        'slug',
        'file',
        'type',
        'attributes',
        'renditions',
    ]

    def get(self, request):
        model_type = request.GET.get('type', 'all')

        try:
            model = self.model_types[model_type]
        except KeyError:
            return JsonResponse({
                'message': 'Unknown value provided for type.'
            }, status=400)


        queryset = model.objects.filter()

        artist = request.GET.get('artist', None)

        if artist != None:
            queryset = queryset.filter(
                attributes__contains={
                    'photographer_artist': artist
                }
            )

        gallery = request.GET.get('gallery', None)

        if gallery != None:
            queryset = queryset.filter(
                attributes__contains={
                    'galleries': [gallery]
                }
            )

        taxon = request.GET.get('taxon', None)

        if taxon != None:
            queryset = queryset.filter(taxon__slug=taxon)


        queryset = queryset.order_by(
            'priority' if taxon else '-created_at'
        )

        skip = abs(int(request.GET.get('skip', 0)))
        limit = abs(int(request.GET.get('limit', 0)))

        if skip > 0 or limit > 0:
            queryset = queryset[skip:(skip + limit)]

        fields = request.GET.get('fields', None)

        if fields == None:
            fields = self.fieldnames
        else:
            fields = list(map(str.strip, fields.split(',')))
            if not all(field in self.fieldnames for field in fields):
                return JsonResponse({
                    'message': 'Unkown value(s) provided for fields.'
                }, status=400)

        return JsonResponse({
            'media': list(queryset.values(*fields))
        })


class ArtistCollectionView(View):

    def get(self, request):
        queryset = Media.objects.all()

        queryset = queryset.values(
            artist=F('attributes__photographer_artist')
        )

        queryset = queryset.annotate(
            number_of_contributions=Count(
                'attributes__photographer_artist'
            )
        )

        queryset = queryset.order_by('-number_of_contributions')

        return JsonResponse({'artists': list(queryset)})
