from django.urls import include, path
from rest_framework.routers import DefaultRouter

from project.api import views

router = DefaultRouter()
router.register("artikel", views.ArtikelViewSet, basename="artikel")
router.register("pp-options", views.PPOptionViewSet, basename="ppoption")
router.register("plattformen", views.PlattformViewSet, basename="plattform")

urlpatterns = [
    path("healthz/", views.HealthzView.as_view(), name="healthz"),
    path("", include(router.urls)),
]
