from django.urls import path
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    path("schema/", views.get_openapi_schema, name="openapi-schema"),
    path("", TemplateView.as_view(template_name="swagger-ui.html")),
]
