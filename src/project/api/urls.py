from django.urls import include, path
from rest_framework.routers import DefaultRouter
from project.api import views

router = DefaultRouter()
router.register("artikel", views.ArtikelViewSet, basename="artikel")
router.register("pp-options", views.PPOptionViewSet, basename="ppoption")
router.register("plattformen", views.PlattformViewSet, basename="plattform")

urlpatterns = [
    path("", include(router.urls)),
]
