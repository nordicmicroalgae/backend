from django.db.models import Q
from django.http import JsonResponse, HttpResponsePermanentRedirect
from django.views import View
from django.urls import reverse

from taxa.models import Synonym, Taxon


class TaxonView(View):

    def get(self, request, scientific_name):
        try:
            taxon = Taxon.objects.get(
                scientific_name__iexact=scientific_name
            )
            return JsonResponse({
                'scientific_name': taxon.scientific_name,
                'parent_name': taxon.parent_name,
                'authority': taxon.authority,
                'rank': taxon.rank,
                'classification': taxon.classification,
                'children': taxon.children,
                'attributes': taxon.attributes,
            })
        except Taxon.DoesNotExist:
            try:
                current_taxon = Synonym.objects.get(
                    scientific_name__iexact=scientific_name
                ).current_name

                return HttpResponsePermanentRedirect(reverse(
                    'taxon', args=[current_taxon.scientific_name]
                ))
            except Synonym.DoesNotExist:
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
                'scientific_name',
                'parent_name',
                'authority',
                'rank',
            ))
        })


class TaxonSynonymCollectionView(View):

    def get(self, request, scientific_name):
        try:
            taxon = Taxon.objects.get(
                scientific_name__iexact=scientific_name
            )
            return JsonResponse({
                'synonyms': list(taxon.synonym_set.all().values(
                    'scientific_name',
                    'authority',
                    'current_name',
                    'additional_info'
                ))
            })
        except Taxon.DoesNotExist:
            return JsonResponse({'message': 'Taxon not found'}, status=404)


class SynonymCollectionView(View):

    def get(self, request):
        conditions = Q()

        name_pattern = request.GET.get('name', None)
        name_pattern = request.GET.get('q', name_pattern) # alias

        if name_pattern != None:
            conditions = conditions & Q(scientific_name__icontains=name_pattern)


        skip = abs(int(request.GET.get('skip', 0)))
        limit = abs(int(request.GET.get('limit', 0)))


        synonyms = Synonym.objects.filter(conditions)

        if skip > 0 or limit > 0:
            synonyms = synonyms[skip:(skip + limit)]

        return JsonResponse({
            'synonyms': list(synonyms.values(
                'scientific_name',
                'authority',
                'current_name'
            ))
        })
