from typing import ClassVar

from django.db.models import Count, F, OuterRef, Q, Subquery
from django.http import Http404, JsonResponse

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

    # Override fields to include priority
    fields = (
        "slug",
        "file",
        "type",
        "created_at",
        "updated_at",
        "attributes",
        "renditions",
        "related_taxon",
        "priority",
    )

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


def image_labeling_summary(request):
    """Return aggregated filter data for image labeling without fetching all images"""

    # Base queryset - only ImageLabeling images
    images = Image.objects.filter(attributes__imagelabeling=True)

    # Count by taxon
    taxa_counts = (
        images.values("taxon__id", "taxon__scientific_name", "taxon__slug")
        .annotate(count=Count("id"))
        .order_by("taxon__scientific_name")
    )

    # Process taxa (handle None taxon)
    taxa_list = []
    for item in taxa_counts:
        if item["taxon__id"] is None:
            taxa_list.append(
                {
                    "id": None,
                    "slug": "__no_taxon__",
                    "name": "Unknown taxon",
                    "count": item["count"],
                }
            )
        else:
            taxa_list.append(
                {
                    "id": item["taxon__id"],
                    "slug": item["taxon__slug"],
                    "name": item["taxon__scientific_name"],
                    "count": item["count"],
                }
            )

    # Get all unique instruments from JSONB
    all_instruments = {}
    for img in images.exclude(attributes__imaging_instrument__isnull=True):
        instruments = img.attributes.get("imaging_instrument", [])
        if not isinstance(instruments, list):
            instruments = [instruments]

        for inst in instruments:
            if inst:
                all_instruments[inst] = all_instruments.get(inst, 0) + 1

    instruments_list = [
        {"name": name, "count": count} for name, count in sorted(all_instruments.items())
    ]

    # Get all unique institutes from JSONB (handle both string and array)
    all_institutes = {}
    for img in images.exclude(attributes__institute__isnull=True):
        institute = img.attributes.get("institute")
        if isinstance(institute, list):
            # TagField - array of institutes
            for inst in institute:
                if inst:
                    all_institutes[inst] = all_institutes.get(inst, 0) + 1
        elif isinstance(institute, str) and institute:
            # CharField - single institute string
            all_institutes[institute] = all_institutes.get(institute, 0) + 1

    institutes_list = [
        {"name": name, "count": count} for name, count in sorted(all_institutes.items())
    ]

    return JsonResponse(
        {
            "taxa": taxa_list,
            "instruments": instruments_list,
            "institutes": institutes_list,
            "total_count": images.count(),
        }
    )


def image_labeling_first_per_taxon(request):
    """Return first image (by priority) per taxon for landing page"""
    from django.db.models import Case, IntegerField, Min, Value, When

    # Get the minimum priority (top priority image) for each taxon
    first_images = (
        Image.objects.filter(attributes__imagelabeling=True)
        .values("taxon_id")
        .annotate(first_priority=Min("priority"))  # Changed from Min("id")
    )

    # Build a list of (taxon_id, priority) pairs to filter
    taxon_priority_pairs = [
        (img["taxon_id"], img["first_priority"]) for img in first_images
    ]

    # Fetch images matching (taxon_id, priority) combinations
    from django.db.models import Q

    query = Q()
    for taxon_id, priority in taxon_priority_pairs:
        query |= Q(taxon_id=taxon_id, priority=priority)

    images = (
        Image.objects.filter(query)
        .filter(attributes__imagelabeling=True)
        .select_related("taxon")
        .annotate(
            taxon_sort=Case(
                When(taxon__isnull=True, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        .order_by("taxon_sort", "taxon__scientific_name")
    )

    # Serialize the response
    results = []
    for img in images:
        result = {
            "slug": img.slug,
            "renditions": img.renditions,
            "attributes": img.attributes,
            "taxon": {
                "slug": img.taxon.slug if img.taxon else None,
                "scientific_name": img.taxon.scientific_name if img.taxon else None,
            }
            if img.taxon
            else None,
            "taxonSlug": img.taxon.slug if img.taxon else "__no_taxon__",
            "taxonName": img.taxon.scientific_name if img.taxon else "Unknown taxon",
        }
        results.append(result)

    return JsonResponse({"images": results})
