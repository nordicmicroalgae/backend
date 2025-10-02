from django.urls import path

from . import views

urlpatterns = [
    path("articles/", views.get_page_list),
    path("articles/<slug:article_id>/", views.get_page),
]
