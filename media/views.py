from typing import ClassVar

from django.db.models import Count, F, OuterRef, Q, Subquery
from django.http import Http404

from core.views.generics import ClientError, CollectionView
from media.models import Image, InvalidTagset, Media
from taxa.models import RelatedTaxon, Taxon


class MediaCollectionView(CollectionView):
    fields = (
        "slug",
        "file",
        "type",
        "created_at",
        "updated_at",
        "attributes",
        "renditions",
        "related_taxon",
    )

    model_types: ClassVar[dict] = {
        "all": Media,
        "image": Image,
    }

    plural_key = "media"

    def get_fields(self, *args, **kwargs):
        fields, expressions = super().get_fields(*args, **kwargs)

        if "related_taxon" in fields:
            related_taxon = RelatedTaxon()
            expressions.update(dict(related_taxon=related_taxon.nullable()))

        return fields, expressions

    def get_queryset(self, *args, **kwargs):
        model_type = self.request.GET.get("type", "all")

        try:
            model = self.model_types[model_type]
        except KeyError:
            raise ClientError("Unknown value provided for type.")

        # start from the chosen model's manager
        queryset = model.objects.all()

        # Exclude IFCB-marked media from the general media collection
        queryset = queryset.filter(
            Q(attributes__imagelabeling__isnull=True) | Q(attributes__imagelabeling=False)
        )

        artist = self.request.GET.get("artist")

        if artist is not None:
            queryset = queryset.filter(
                attributes__contains={"photographer_artist": artist}
            )

        gallery = self.request.GET.get("gallery")

        if gallery is not None:
            queryset = queryset.filter(attributes__contains={"galleries": [gallery]})

        # Add exclude_galleries parameter
        exclude_galleries = self.request.GET.get("exclude_galleries")

        if exclude_galleries is not None:
            # Exclude images that have this gallery in their galleries list
            queryset = queryset.exclude(
                attributes__contains={"galleries": [exclude_galleries]}
            )

        taxon = self.request.GET.get("taxon", "")

        if taxon:
            if self.request.GET.get("children", "").lower() == "true":
                possible_taxons = [
                    child["slug"]
                    for child in Taxon.objects.filter(slug=taxon)
                    .values_list("children", flat=True)
                    .first()
                    or []
                    if "slug" in child
                ]
            else:
                possible_taxons = [taxon]

            queryset = queryset.filter(taxon__slug__in=possible_taxons)

        if self.request.GET.get("priority", "").lower() == "true":
            prioritized_media = (
                model.objects.filter(taxon=OuterRef("taxon"))
                .order_by("priority", "id")
                .values("id")[:1]
            )
            queryset = queryset.filter(id__in=Subquery(prioritized_media))
        else:
            queryset = queryset.order_by("priority" if taxon else "-created_at")

        return queryset


class ArtistCollectionView(CollectionView):
    queryset = Media.objects

    fields = (
        "artist",
        "number_of_contributions",
    )

    plural_key = "artists"

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.values(artist=F("attributes__photographer_artist"))

        queryset = queryset.annotate(
            number_of_contributions=Count("attributes__photographer_artist")
        )

        queryset = queryset.order_by("-number_of_contributions")

        return queryset


class TagCollectionView(CollectionView):
    fields = ("name",)
    plural_key = "tags"

    def get_queryset(self, *args, **kwargs):
        try:
            queryset = Media.objects.get_tagset(
                self.request.resolver_match.kwargs.get("tagset")
            )
        except InvalidTagset:
            raise Http404()

        return queryset


# -----------------------
# ImageLabeling-specific endpoints
# -----------------------


class ImageLabelingCollectionView(MediaCollectionView):
    """
    A collection view that returns only images marked for ImageLabeling.

    Inherits field configuration and other behavior from MediaCollectionView
    but implements its own queryset building so it doesn't inherit the
    global exclusion of ImageLabeling images added to MediaCollectionView.
    """

    plural_key = "image_labeling_images"

    def get_queryset(self, *args, **kwargs):
        model = Image  # or your ImageLabeling proxy model if you have one
        queryset = model.objects.all()

        artist = self.request.GET.get("artist")
        if artist is not None:
            queryset = queryset.filter(
                attributes__contains={"photographer_artist": artist}
            )

        gallery = self.request.GET.get("gallery")
        if gallery is not None:
            queryset = queryset.filter(attributes__contains={"galleries": [gallery]})

        taxon = self.request.GET.get("taxon", "")
        if taxon:
            if self.request.GET.get("children", "").lower() == "true":
                possible_taxons = [
                    child["slug"]
                    for child in Taxon.objects.filter(slug=taxon)
                    .values_list("children", flat=True)
                    .first()
                    or []
                    if "slug" in child
                ]
            else:
                possible_taxons = [taxon]

            queryset = queryset.filter(taxon__slug__in=possible_taxons)

        if self.request.GET.get("priority", "").lower() == "true":
            prioritized_media = (
                model.objects.filter(taxon=OuterRef("taxon"))
                .order_by("priority", "id")
                .values("id")[:1]
            )
            queryset = queryset.filter(id__in=Subquery(prioritized_media))
        else:
            queryset = queryset.order_by("priority" if taxon else "-created_at")

        # Only include images flagged for ImageLabeling
        queryset = queryset.filter(attributes__imagelabeling=True)

        return queryset

from django.http import JsonResponse


def image_labeling_summary(request):
    """Return aggregated filter data for image labeling without fetching all images"""
    
    # Base queryset - only ImageLabeling images
    images = Image.objects.filter(attributes__imagelabeling=True)
    
    # Count by taxon
    taxa_counts = images.values(
        'taxon__id',
        'taxon__scientific_name',
        'taxon__slug'
    ).annotate(
        count=Count('id')
    ).order_by('taxon__scientific_name')
    
    # Process taxa (handle None taxon)
    taxa_list = []
    for item in taxa_counts:
        if item['taxon__id'] is None:
            taxa_list.append({
                'id': None,
                'slug': '__no_taxon__',
                'name': 'Unknown taxon',
                'count': item['count']
            })
        else:
            taxa_list.append({
                'id': item['taxon__id'],
                'slug': item['taxon__slug'],
                'name': item['taxon__scientific_name'],
                'count': item['count']
            })
    
    # Get all unique instruments from JSONB
    all_instruments = {}
    for img in images.exclude(attributes__imagingInstrument__isnull=True):
        instruments = img.attributes.get('imagingInstrument', [])
        if not isinstance(instruments, list):
            instruments = [instruments]
        
        for inst in instruments:
            if inst:
                all_instruments[inst] = all_instruments.get(inst, 0) + 1
    
    instruments_list = [
        {'name': name, 'count': count}
        for name, count in sorted(all_instruments.items())
    ]
    
    # Get all unique institutes from JSONB (handle both string and array)
    all_institutes = {}
    for img in images.exclude(attributes__institute__isnull=True):
        institute = img.attributes.get('institute')
        if isinstance(institute, list):
            # TagField - array of institutes
            for inst in institute:
                if inst:
                    all_institutes[inst] = all_institutes.get(inst, 0) + 1
        elif isinstance(institute, str) and institute:
            # CharField - single institute string
            all_institutes[institute] = all_institutes.get(institute, 0) + 1
    
    institutes_list = [
        {'name': name, 'count': count}
        for name, count in sorted(all_institutes.items())
    ]
    
    return JsonResponse({
        'taxa': taxa_list,
        'instruments': instruments_list,
        'institutes': institutes_list,
        'total_count': images.count()
    })