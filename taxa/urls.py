from django.urls import path


from taxa.views import (
   TaxonView,
   TaxonCollectionView,
   TaxonSynonymCollectionView,
   SynonymCollectionView
)

urlpatterns = [
    path('taxa/<str:slug>/', TaxonView.as_view(), name='taxon'),
    path('taxa/', TaxonCollectionView.as_view(), name='taxon-collection'),
    path('synonyms/<str:scientific_name>/', TaxonSynonymCollectionView.as_view(), name='taxon-synonym-collection'),
    path('synonyms/', SynonymCollectionView.as_view(), name='synonym-collection'),
]
