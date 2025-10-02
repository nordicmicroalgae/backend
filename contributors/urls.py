from django.urls import path

from contributors.views import ContributorCollectionView

urlpatterns = [
    path(
        "contributors/",
        ContributorCollectionView.as_view(),
        name="contributor-collection",
    ),
]
