from django.urls import path
from project.core import views

app_name = "core"

urlpatterns = [
    path("", views.ArtikelListeView.as_view(), name="artikel-liste"),
    path("artikel/neu/", views.ArtikelAnlegenView.as_view(), name="artikel-anlegen"),
    path("artikel/<int:pk>/bearbeiten/", views.ArtikelBearbeitenView.as_view(), name="artikel-bearbeiten"),
    path("artikel/<int:pk>/", views.ArtikelDetailView.as_view(), name="artikel-detail"),
]
