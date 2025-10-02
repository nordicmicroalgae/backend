from typing import ClassVar

from django.db.models import Count, F
from django.http import Http404

from core.views.generics import ClientError, CollectionView
from media.models import Image, InvalidTagset, Media
from taxa.models import RelatedTaxon


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

        taxon = self.request.GET.get("taxon")

        if taxon is not None:
            queryset = queryset.filter(taxon__slug=taxon)

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
