from django.urls import path


from facts.views import TaxonFactsCollectionView

urlpatterns = [
    path('facts/<str:slug>/', TaxonFactsCollectionView.as_view(), name='taxon-facts-collection'),
]
