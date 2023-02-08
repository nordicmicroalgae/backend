from django.urls import path

from media.views import (
    MediaCollectionView,
)


urlpatterns = [
    path('media/', MediaCollectionView.as_view(), name='media-collection-view'),
]