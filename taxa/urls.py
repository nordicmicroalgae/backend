from django.urls import path


from taxa.views import (
   TaxonView,
   TaxonCollectionView,
   SynonymCollectionView,
)

urlpatterns = [
    path('taxa/<str:slug>/', TaxonView.as_view(), name='taxon'),
    path('taxa/', TaxonCollectionView.as_view(), name='taxon-collection'),
    path('synonyms/', SynonymCollectionView.as_view(), name='synonym-collection'),
]
