from django.urls import path

from media.views import (
    ArtistCollectionView,
    ImageLabelingCollectionView,
    MediaCollectionView,
    TagCollectionView,
    image_labeling_first_per_taxon,
    image_labeling_grouped_by_plankton,
    image_labeling_summary,
)

urlpatterns = [
    path(
        "media/",
        MediaCollectionView.as_view(),
        name="media-collection-view",
    ),
    path(
        "media/artists/",
        ArtistCollectionView.as_view(),
        name="artist-collection-view",
    ),
    path(
        "media/tags/<str:tagset>/",
        TagCollectionView.as_view(),
        name="tag-collection-view",
    ),
    # ImageLabeling-specific endpoints
    path(
        "media/image_labeling/",
        ImageLabelingCollectionView.as_view(),
        name="image-labeling-collection-view",
    ),
    path(
        "media/image_labeling/summary/",
        image_labeling_summary,
        name="image-labeling-summary",
    ),
    path(
        "media/image_labeling/first_per_taxon/",
        image_labeling_first_per_taxon,
        name="image-labeling-first-per-taxon",
    ),
    path(
        "media/image_labeling/grouped_by_plankton/",
        image_labeling_grouped_by_plankton,
        name="image-labeling-grouped-by-plankton",
    ),
]
