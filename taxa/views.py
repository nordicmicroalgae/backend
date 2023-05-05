from django.db.models import Count, OuterRef, Subquery
from django.http import JsonResponse
from django.views import View

from taxa.models import Taxon
from media.models import Image


class TaxonView(View):

    def get(self, request, slug):
        try:
            taxon = Taxon.objects.get(
                slug__iexact=slug
            )
            return JsonResponse({
                'slug': taxon.slug,
                'scientific_name': taxon.scientific_name,
                'authority': taxon.authority,
                'rank': taxon.rank,
                'parent': taxon.parent,
                'classification': taxon.classification,
                'children': taxon.children,
            })
        except Taxon.DoesNotExist:
            return JsonResponse({'message': 'Taxon not found'}, status=404)


class TaxonCollectionView(View):

    fieldnames = [
        'slug',
        'scientific_name',
        'authority',
        'rank',
        'parent',
        'classification',
        'children',
        'image',
    ]

    def get(self, request):
        queryset = Taxon.objects.filter()

        name_pattern = request.GET.get('name', None)

        if name_pattern != None:
            queryset = queryset.with_name_like(name_pattern)


        group = request.GET.get('group', None)

        if group != None:
            try:
                queryset = queryset.within_group(group)
            except queryset.InvalidQuery as exc:
                return JsonResponse({
                    'message': str(exc)
                }, status=400)


        helcom_peg_only = request.GET.get('helcom-peg-only') == 'true'

        if helcom_peg_only:
            queryset = queryset.helcom_peg_only()


        illustrated_only = (
            request.GET.get('illustrated-only') == 'true'
        )
        not_illustrated_only = (
            request.GET.get('not-illustrated-only') == 'true'
        )

        if illustrated_only and not_illustrated_only:
            return JsonResponse({
                'message': (
                    'It is not possible to combine '
                    'illustrated-only and not-illustrated-only.'
                )
            }, status=400)

        if illustrated_only or not_illustrated_only:
            queryset = queryset.annotate(image_count=Count('media'))
            if illustrated_only:
                queryset = queryset.filter(image_count__gt=0)
            elif not_illustrated_only:
                queryset = queryset.filter(image_count=0)


        offset = abs(int(request.GET.get('offset', 0)))
        limit = abs(int(request.GET.get('limit', 0)))

        if offset > 0 or limit > 0:
            if limit > 0:
                queryset = queryset[offset:(offset + limit)]
            else:
                queryset = queryset[offset:]


        fields = request.GET.get('fields', None)

        if fields == None:
            fields = self.fieldnames
        else:
            fields = list(map(str.strip, fields.split(',')))
            if not all(field in self.fieldnames for field in fields):
                return JsonResponse({
                    'message': 'Unkown value provided for fields.'
                }, status=400)

        if 'image' in fields:
            subqueryset = (
                Image.objects.filter(taxon=OuterRef('pk')).order_by('priority')
            )
            queryset = queryset.annotate(
                image=Subquery(subqueryset.values('renditions')[:1])
            )

        return JsonResponse({
            'taxa': list(queryset.values(*fields))
        })
