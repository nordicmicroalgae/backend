from django.urls import path


from . import views

urlpatterns = [
    path('pages/<page_slug>/', views.get_page),
]