"""DRF-Serializers — Artikel, P&P, Plattform, Bilder, Status."""

from decimal import Decimal

from rest_framework import serializers

from project.core.models import (
    Artikel,
    Bild,
    BildSource,
    BildSymbol,
    Kategorie,
    PlatformStatus,
    Plattform,
    PPOption,
)


class KategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kategorie
        fields = ["id", "name", "parent"]


class BildSymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = BildSymbol
        fields = ["id", "bezeichnung", "beschreibung"]


class PPOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PPOption
        fields = ["id", "bezeichnung", "kosten", "beschreibung", "is_default"]
        read_only_fields = ["is_default"]


class BildSerializer(serializers.ModelSerializer):
    """Read-Only-Darstellung: Pfad (upload) ODER Symbol-Bez (symbol)."""

    symbol_detail = BildSymbolSerializer(source="symbol", read_only=True)

    class Meta:
        model = Bild
        fields = [
            "id",
            "source",
            "pfad",
            "symbol",
            "symbol_detail",
            "alt_text",
            "position",
            "is_primary",
        ]
        read_only_fields = [
            "id",
            "source",
            "pfad",
            "symbol",
            "alt_text",
            "position",
            "is_primary",
        ]


class PlatformStatusSerializer(serializers.ModelSerializer):
    platform_name = serializers.CharField(source="platform.name", read_only=True)

    class Meta:
        model = PlatformStatus
        fields = [
            "id",
            "platform",
            "platform_name",
            "status",
            "externe_id",
            "letzte_sync",
            "letzte_fehlermeldung",
        ]


class ArtikelSerializer(serializers.ModelSerializer):
    """Read-Only-Darstellung (mit Bildern, Status und abgeleiteten Feldern)."""

    images = BildSerializer(source="bilder", many=True, read_only=True)
    plattformstatus = PlatformStatusSerializer(source="plattformstatus_set", many=True, read_only=True)

    # Abgeleitete Felder — explizit deklariert (ModelSerializer kennt sie nicht)
    rest_verfügbar = serializers.IntegerField(read_only=True)
    pp_bezeichnung = serializers.SerializerMethodField()
    pp_kosten = serializers.SerializerMethodField()
    kategorie_name = serializers.SerializerMethodField()

    class Meta:
        model = Artikel
        fields = [
            "id",
            "titel",
            "beschreibung",
            "kategorie",
            "kategorie_name",
            "zustand",
            "preis",
            "pp_option",
            "pp_bezeichnung",
            "pp_kosten",
            "anzahl_verfügbar",
            "anzahl_verkauft",
            "rest_verfügbar",
            "verkauft",
            "images",
            "plattformstatus",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "rest_verfügbar",
            "anzahl_verkauft",
            "verkauft",
            "created_at",
            "updated_at",
        ]

    def get_pp_bezeichnung(self, obj) -> str | None:
        return obj.pp_option.bezeichnung if obj.pp_option else None

    def get_pp_kosten(self, obj) -> Decimal | None:
        return obj.pp_option.kosten if obj.pp_option else None

    def get_kategorie_name(self, obj) -> str | None:
        return obj.kategorie.name if obj.kategorie else None


class ArtikelInputSerializer(serializers.ModelSerializer):
    """Schmale Eingabe für Create/Update — nur die wählbaren Basisfelder.

    Bilder & Plattformstatus werden über eigene Endpunkte gepflegt.
    """

    class Meta:
        model = Artikel
        fields = [
            "id",
            "titel",
            "beschreibung",
            "kategorie",
            "zustand",
            "preis",
            "pp_option",
            "anzahl_verfügbar",
            "anzahl_verkauft",
            "verkauft",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs.get("anzahl_verfügbar") is not None and attrs["anzahl_verfügbar"] < 0:
            raise serializers.ValidationError({"anzahl_verfügbar": "muss ≥ 0 sein"})
        return attrs


class PlattformSerializer(serializers.ModelSerializer):
    """Read-Only — Änderungen über den Admin (konfiguration ist vertraulich)."""

    class Meta:
        model = Plattform
        fields = ["id", "name", "adapter_slug", "is_aktiv"]
        read_only_fields = ["id", "name", "adapter_slug", "is_aktiv"]


# Hinweis: ``platform_name``/``symbol_detail`` etc. sind nur für die Lesbarkeit.
class BildInputSerializer(serializers.Serializer):
    """Serieller Input: source=upload+pfad ODER source=symbol+symbol_id.

    Exklusivität wird über den DB-Constraint ``bild_source_exklusiv`` abgesichert.
    """

    source = serializers.ChoiceField(choices=BildSource.choices)
    pfad = serializers.CharField(required=False, allow_blank=True)
    symbol = serializers.PrimaryKeyRelatedField(queryset=BildSymbol.objects.all(), required=False)
    alt_text = serializers.CharField(required=False, allow_blank=True, max_length=255)
    position = serializers.IntegerField(min_value=0, default=0)
    is_primary = serializers.BooleanField(default=False)
