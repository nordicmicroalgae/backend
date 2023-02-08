from django.urls import path

from media.views import (
    ArtistCollectionView,
    MediaCollectionView,
)


urlpatterns = [
    path('media/', MediaCollectionView.as_view(), name='media-collection-view'),
    path('media/artists/', ArtistCollectionView.as_view(), name='artist-collection-view'),
]