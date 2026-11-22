from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from project.api.serializers import (
    ArtikelInputSerializer,
    ArtikelSerializer,
    PlattformSerializer,
    PPOptionSerializer,
)
from project.core.models import Artikel, Plattform, PPOption


class ArtikelViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
    queryset = Artikel.objects.select_related("pp_option", "kategorie").prefetch_related(
        "bilder", "plattformstatus_set"
    )
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return ArtikelInputSerializer
        return ArtikelSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Filter: ``?verkauft=true|false`` — nur wenn der Parameter gesetzt ist
        raw = self.request.query_params.get("verkauft")
        if raw is not None:
            value = str(raw).strip().lower() == "true"
            qs = qs.filter(verkauft=value)
        return qs


class PPOptionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PPOption.objects.all()
    serializer_class = PPOptionSerializer
    permission_classes = [IsAuthenticated]


class PlattformViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plattform.objects.filter(is_aktiv=True)
    serializer_class = PlattformSerializer
    permission_classes = [IsAuthenticated]


class HealthzView(APIView):
    """Liveness-Check für Container-Probes (Docker HEALTHCHECK, k8s) — ohne DB-Zugriff."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return JsonResponse({"status": "ok"})
