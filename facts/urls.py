from django.urls import path


from facts.views import TaxonFactsCollectionView

urlpatterns = [
    path('facts/<str:scientific_name>/', TaxonFactsCollectionView.as_view(), name='taxon-facts-collection'),
]
