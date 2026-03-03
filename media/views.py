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
        include_subgalleries = (
            self.request.GET.get("include_subgalleries", "true").lower() not in {"false", "0"}
        )

        if gallery is not None:
            if include_subgalleries:
                queryset = queryset.filter(
                    Q(attributes__contains={"galleries": [gallery]})
                    | Q(attributes__galleries__icontains=f"{gallery}/")
                )
            else:
                queryset = queryset.filter(attributes__contains={"galleries": [gallery]})

        exclude_galleries = self.request.GET.get("exclude_galleries")

        if exclude_galleries is not None:
            # Exclude images that have this gallery in their galleries list
            queryset = queryset.exclude(
                Q(attributes__contains={"galleries": [exclude_galleries]})
                | Q(attributes__galleries__icontains=f"{exclude_galleries}/")
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
        model = Image
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
                    "slug": "unknown",
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

    # Count images with no institute
    no_institute_count = images.filter(
        Q(attributes__institute__isnull=True)
        | Q(attributes__institute="")
        | Q(attributes__institute=[])
    ).count()

    if no_institute_count > 0:
        all_institutes["__not_specified__"] = no_institute_count

    institutes_list = [
        {"name": name, "count": count} for name, count in sorted(all_institutes.items())
    ]

    # Get all unique geographic areas from JSONB
    all_geographic_areas = {}
    for img in images.exclude(attributes__geographic_area__isnull=True):
        geographic_area = img.attributes.get("geographic_area")
        if geographic_area:
            all_geographic_areas[geographic_area] = (
                all_geographic_areas.get(geographic_area, 0) + 1
            )

    # Count images with no geographic_area
    no_area_count = images.filter(
        Q(attributes__geographic_area__isnull=True) | Q(attributes__geographic_area="")
    ).count()

    if no_area_count > 0:
        all_geographic_areas["__not_specified__"] = no_area_count

    geographic_areas_list = [
        {"name": name, "count": count}
        for name, count in sorted(all_geographic_areas.items())
    ]

    return JsonResponse(
        {
            "taxa": taxa_list,
            "instruments": instruments_list,
            "institutes": institutes_list,
            "geographic_areas": geographic_areas_list,
            "total_count": images.count(),
        }
    )


def image_labeling_grouped_by_plankton(request):
    """Return taxa grouped by plankton groups with unique class names per taxon."""
    from taxa.models import get_filter_config

    # Load the groups config
    config = get_filter_config()
    groups_config = config.get("groups_of_organisms", [])

    # Define the display order (excluding "Other microalgae" - those go to "Other")
    group_order = [
        "Cyanobacteria",
        "Diatoms",
        "Dinoflagellates",
        "Ciliates",
        "Protozoa",
    ]

    # Build a lookup: group_name -> set of parent taxa scientific names
    # Only include groups that are in our display order
    groups_parents = {}
    for group in groups_config:
        if group["group_name"] in group_order:
            groups_parents[group["group_name"]] = set(group["included_taxa"])

    # Get all image labeling images with taxa
    images = (
        Image.objects.filter(attributes__imagelabeling=True)
        .select_related("taxon")
        .only("taxon", "attributes")
    )

    # Build data structure: { taxon_slug: { taxon_name, classification, titles } }
    taxa_data = {}
    for img in images:
        if not img.taxon:
            continue

        taxon_slug = img.taxon.slug
        title = img.attributes.get("title", "Untitled")

        if taxon_slug not in taxa_data:
            taxa_data[taxon_slug] = {
                "taxon_slug": taxon_slug,
                "taxon_name": img.taxon.scientific_name,
                "classification": img.taxon.classification or [],
                "titles": set(),
            }
        taxa_data[taxon_slug]["titles"].add(title)

    # Determine which group each taxon belongs to
    def get_taxon_group(taxon_name, classification):
        """Check which group a taxon belongs to based on its name or classification"""
        # Build set of names to check: the taxon's own name + all ancestors
        classification_names = {
            c.get("scientific_name") for c in classification if isinstance(c, dict)
        }
        # Also include the taxon's own scientific name
        names_to_check = classification_names | {taxon_name}

        for group_name in group_order:
            if group_name in groups_parents:
                parents = groups_parents[group_name]
                # Check if any of the taxon's names match the group's included taxa
                if names_to_check & parents:
                    return group_name
        return None

    # Organize taxa by groups
    groups_data = {group: [] for group in group_order}
    unassigned_taxa = []

    for taxon_slug, data in taxa_data.items():
        group = get_taxon_group(data["taxon_name"], data["classification"])
        taxon_entry = {
            "taxon_slug": data["taxon_slug"],
            "taxon_name": data["taxon_name"],
            "titles": sorted(list(data["titles"])),
            "title_count": len(data["titles"]),
        }
        if group:
            groups_data[group].append(taxon_entry)
        else:
            unassigned_taxa.append(taxon_entry)

    # Sort taxa within each group alphabetically
    for group in groups_data:
        groups_data[group].sort(key=lambda x: x["taxon_name"])
    unassigned_taxa.sort(key=lambda x: x["taxon_name"])

    # Build response in the requested order
    result = []
    for group_name in group_order:
        taxa = groups_data.get(group_name, [])
        if taxa:  # Only include groups that have taxa with images
            result.append(
                {
                    "group_name": group_name,
                    "taxa": taxa,
                    "taxon_count": len(taxa),
                }
            )

    # Add unassigned taxa to "Other" if any
    if unassigned_taxa:
        result.append(
            {
                "group_name": "Other",
                "taxa": unassigned_taxa,
                "taxon_count": len(unassigned_taxa),
            }
        )

    return JsonResponse({"groups": result})


def image_labeling_first_per_taxon(request):
    """Return first image (by priority) per taxon for landing page"""
    from django.db.models import Case, IntegerField, Min, Value, When

    # Get the minimum priority (top priority image) for each taxon
    first_images = (
        Image.objects.filter(attributes__imagelabeling=True)
        .values("taxon_id")
        .annotate(first_priority=Min("priority"))
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
            "taxonSlug": img.taxon.slug if img.taxon else "unknown",
            "taxonName": img.taxon.scientific_name if img.taxon else "Unknown taxon",
        }
        results.append(result)

    return JsonResponse({"images": results})
