from django.db.models import Q
from django.http import JsonResponse

from taxa.models import Synonym, Taxon


def get_taxon(request, scientific_name):
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
        return JsonResponse({'message': 'Taxon not found'}, status=404)


def get_taxa(request):
    conditions = Q()


    name_pattern = request.GET.get('name', None)

    if name_pattern != None:
        conditions = conditions & Q(scientific_name__contains=name_pattern)


    rank = request.GET.get('rank', None)

    if rank != None:
        conditions = conditions & Q(rank__iexact=rank)


    skip = abs(int(request.GET.get('skip', 0)))
    limit = abs(int(request.GET.get('limit', 0)))


    taxa = Taxon.objects.filter(conditions)

    if skip > 0 or limit > 0:
        taxa = taxa[skip:(skip + limit)]

    return JsonResponse({
        'taxa': list(taxa.values(
            'scientific_name',
            'parent_name',
            'authority',
            'rank',
        ))
    })


def get_taxon_synonyms(request, scientific_name):
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


def get_synonyms(request):
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
