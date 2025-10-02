from django.http import JsonResponse
from django.views import View

from taxa.models import Taxon


class TaxonFactsCollectionView(View):
    def get(self, request, slug):
        try:
            taxon = Taxon.objects.get(slug=slug)
            return JsonResponse({"facts": taxon.facts.data})
        except Taxon.DoesNotExist:
            return JsonResponse({"message": "Taxon not found"}, status=404)
        except Taxon.facts.RelatedObjectDoesNotExist:
            return JsonResponse({"message": "Facts not found"}, status=404)
