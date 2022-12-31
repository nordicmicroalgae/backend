from django.http import JsonResponse
from django.views import View

from taxa.models import Taxon


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

    def get(self, request):
        queryset = Taxon.objects.filter()

        name_pattern = request.GET.get('name', None)

        if name_pattern != None:
            queryset = queryset.with_name_like(name_pattern)


        group = request.GET.get('group', None)

        if group == 'all':
            queryset = queryset.species_only()
        elif group == 'cyanobacteria':
            queryset = queryset.cyanobacteria_only()
        elif group == 'diatoms':
            queryset = queryset.diatoms_only()
        elif group == 'dinoflagellates':
            queryset = queryset.dinoflagellates_only()
        elif group == 'ciliates':
            queryset = queryset.ciliates_only()
        elif group == 'other-microalgae':
            queryset = queryset.other_microalgae_only()
        elif group == 'other-protozoa':
            queryset = queryset.other_protozoa_only()


        harmful_only = request.GET.get('harmful-only') == 'true'

        if harmful_only:
            queryset = queryset.harmful_only()


        helcom_peg_only = request.GET.get('helcom-peg-only') == 'true'

        if helcom_peg_only:
            queryset = queryset.helcom_peg_only()


        skip = abs(int(request.GET.get('skip', 0)))
        limit = abs(int(request.GET.get('limit', 0)))

        if skip > 0 or limit > 0:
            queryset = queryset[skip:(skip + limit)]


        return JsonResponse({
            'taxa': list(queryset.values(
                'slug',
                'scientific_name',
                'authority',
                'rank',
                'parent',
            ))
        })
