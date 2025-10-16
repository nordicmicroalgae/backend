from typing import ClassVar

from django.db.models import Count, F, OuterRef, Subquery
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
