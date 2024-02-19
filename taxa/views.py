from django.db.models import Count, OuterRef, Subquery

from core.views.generics import CollectionView, ResourceView, ClientError
from taxa.models import Taxon, RelatedTaxon, Synonym
from media.models import Image


class TaxonView(ResourceView):
    queryset = Taxon.objects

    fields = (
        'slug',
        'scientific_name',
        'authority',
        'rank',
        'parent',
        'classification',
        'children',
    )


class TaxonCollectionView(CollectionView):
    queryset = Taxon.objects

    fields = (
        'slug',
        'scientific_name',
        'authority',
        'rank',
        'parent',
        'classification',
        'children',
        'image',
    )

    plural_key = 'taxa'

    def get_fields(self, *args, **kwargs):
        fields, expressions = super().get_fields(*args, **kwargs)

        if 'image' in fields:
            subqueryset = (
                Image.objects.filter(taxon=OuterRef('pk')).order_by('priority')
            )
            expressions.update({
                'image': Subquery(subqueryset.values('renditions')[:1]),
            })

        return fields, expressions

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)

        name_pattern = self.request.GET.get('name')

        if name_pattern != None:
            queryset = queryset.with_name_like(name_pattern)


        rank = self.request.GET.get('rank')

        if rank != None:
            queryset = queryset.within_rank(rank)


        group = self.request.GET.get('group')

        if group != None:
            try:
                queryset = queryset.within_group(group)
            except queryset.InvalidQuery as exc:
                raise ClientError(str(exc)) from exc


        helcom_peg_only = (
            self.request.GET.get('helcom-peg-only') == 'true'
        )

        if helcom_peg_only:
            queryset = queryset.helcom_peg_only()


        illustrated_only = (
            self.request.GET.get('illustrated-only') == 'true'
        )
        not_illustrated_only = (
            self.request.GET.get('not-illustrated-only') == 'true'
        )

        if illustrated_only and not_illustrated_only:
            raise ClientError(
                'It is not possible to combine '
                'illustrated-only and not-illustrated-only.'
            )

        if illustrated_only or not_illustrated_only:
            queryset = queryset.annotate(image_count=Count('media'))
            if illustrated_only:
                queryset = queryset.filter(image_count__gt=0)
            elif not_illustrated_only:
                queryset = queryset.filter(image_count=0)

        queryset = queryset.order_by('scientific_name')

        return queryset


class SynonymCollectionView(CollectionView):
    queryset = Synonym.objects

    fields = (
        'authority',
        'synonym_name',
        'related_taxon',
    )

    plural_key = 'synonyms'

    def get_fields(self, *args, **kwargs):
        fields, expressions = super().get_fields(*args, **kwargs)

        if 'related_taxon' in fields:
            expressions.update(dict(
                related_taxon=RelatedTaxon()
            ))

        return fields, expressions

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)

        taxon = self.request.GET.get('taxon')

        if taxon != None:
            queryset = queryset.filter(taxon__slug=taxon)

        return queryset
