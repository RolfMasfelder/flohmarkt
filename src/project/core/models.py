"""Domain-Modell — v1 (2026-11-20, mit Rolf festgelegt).

Kernprinzipien:
- **Ein Preis pro Artikel**: ``Artikel.preis`` ist der Basispreis.
  Später: ``PlatformStatus.preis_override`` für Gebühren/Abweichungen
  pro Plattform.
- **P&P separat** (``PPOption``): Artikel referenziert über FK.
  Default = 0 € = Selbstabholung.
- **Bilder** in zwei Quellen:
  - ``Bild`` mit ``source=upload`` (echtes Upload), oder
  - ``Bild`` mit ``source=symbol`` + Bezug auf ``BildSymbol``.
- **Anzahl verfügbar**: 1 Teller 5× → ``anzahl_verfügbar = 5``.
"""

from decimal import Decimal
from pathlib import Path

from django.conf import settings as django_settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone


def _default_pp_option_pk() -> int | None:
    """Callable-Default: id der Standard-P&P-Option (0 € = Selbstabholung)."""
    obj = PPOption.objects.filter(is_default=True).order_by("id").first()
    return obj.id if obj else None


# ---------------------------------------------------------------------------
# Enumerated choices (Django-style — als CharField + choices, nicht FK)
# ---------------------------------------------------------------------------
class Zustand(models.TextChoices):
    NEU = "neu", "Neu"
    GEBRAUCHT = "gebraucht", "Gebraucht"
    DEFEKT_FUNKTIONAL = "defekt_funktional", "Defekt (funktional)"
    DEFEKT = "defekt", "Defekt"


class PlattformStatusStatus(models.TextChoices):
    AKTIV = "aktiv", "Aktiv"
    INAKTIV = "inaktiv", "Inaktiv"
    GESPERRT = "gesperrt", "Gesperrt"
    FEHLGESCHLAGEN = "fehlgeschlagen", "Fehlgeschlagen"


class BildSource(models.TextChoices):
    UPLOAD = "upload", "Upload"
    SYMBOL = "symbol", "Symbolbild"


# ---------------------------------------------------------------------------
# Plattform
# ---------------------------------------------------------------------------
class Plattform(models.Model):
    """Eine angebundene Plattform (Kleinanzeigen, eBay, …).

    ``konfiguration`` (JSONB) hält alles Plattformspezifische
    (endpoints, Zeitfenster, Credentials-Referenzen). Nicht-secret
    bleibt hier, Secrets zwingend extern (env/Secrets-Manager).
    """

    name = models.CharField(max_length=50, unique=True)
    adapter_slug = models.CharField(max_length=50, help_text="Python-Modul/Adapter, der diese Plattform bedient.")
    konfiguration = models.JSONField(default=dict, blank=True)
    is_aktiv = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Plattform"
        verbose_name_plural = "Plattformen"

    def __str__(self) -> str:
        return self.name

    def get_adapter(self):
        """Returniert den Adapter-Instanz für ``adapter_slug``.

        Lazy + Registry-basiert (in ``project.core.adapter_registry``).
        """
        from project.core import adapter_registry  # local import zur Vermeidung von Zyklen

        return adapter_registry.get(self.adapter_slug)


# ---------------------------------------------------------------------------
# Kategorie (optional, hierarchisch)
# ---------------------------------------------------------------------------
class Kategorie(models.Model):
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Kategorie"
        verbose_name_plural = "Kategorien"

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# P&P-Option — separate Tabelle, 0-€-Default = Selbstabholung
# ---------------------------------------------------------------------------
class PPOption(models.Model):
    bezeichnung = models.CharField(max_length=120)
    kosten = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    beschreibung = models.TextField(blank=True)
    is_default = models.BooleanField(default=False, help_text="Genau eine Option trägt True.")

    class Meta:
        ordering = ["kosten", "bezeichnung"]
        verbose_name = "P&P-Option"
        verbose_name_plural = "P&P-Optionen"

        constraints = [
            # Exakt eine Default-Option pro „Scope" — V1: eine globale.
            # (Constraint über ein Check/Unique-Modell in der App-Migration
            #  wird bei Bedarf ergänzt.)
        ]

    def __str__(self) -> str:
        return f"{self.bezeichnung} ({self.kosten:,.2f} €)".replace(",", "")

    # (Default-Auflösung über die module-funktion ``_default_pp_option_pk``)


# ---------------------------------------------------------------------------
# Artikel — die zentrale Entität
# ---------------------------------------------------------------------------
class Artikel(models.Model):
    titel = models.CharField(max_length=150)
    beschreibung = models.TextField()

    kategorie = models.ForeignKey(
        Kategorie,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="artikel",
    )

    zustand = models.CharField(
        max_length=20,
        choices=Zustand.choices,
        default=Zustand.GEBRAUCHT,
    )

    # V1: ein fester Basispreis. Später: PlatformStatus.preis_override.
    preis = models.DecimalField(max_digits=10, decimal_places=2)

    pp_option = models.ForeignKey(
        PPOption,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="artikel",
        default=_default_pp_option_pk,  # callable → id der Default-Option (0 € = Selbstabholung)
        help_text="Paket & Porto-Option. 0-€-Option = Selbstabholung.",
    )

    anzahl_verfügbar = models.PositiveIntegerField(
        default=1,
        help_text="Wie viele identische Exemplare sind verfügbar (z. B. ein Motiv, 5× Teller).",
    )
    anzahl_verkauft = models.PositiveIntegerField(default=0, help_text="Count der verkauften Exemplare.")

    verkauft = models.BooleanField(default=False, help_text="Schnell-Flag: alles ist weg.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Artikel"
        verbose_name_plural = "Artikel"

    def __str__(self) -> str:
        return f"{self.titel} — {self.preis:,.2f} €"

    def get_absolute_url(self) -> str:
        from django.urls import reverse
        return reverse("core:artikel-detail", args=[self.pk])

    # -- Helpers -------------------------------------------------------------
    @property
    def rest_verfügbar(self) -> int:
        return max(0, self.anzahl_verfügbar - self.anzahl_verkauft)

    @property
    def pp_kosten(self) -> Decimal | None:
        """P&P-Kosten laut gewählter Option (0 € → Selbstabholung)."""
        return self.pp_option.kosten if self.pp_option else None


# ---------------------------------------------------------------------------
# Bild-Symbol (Bibliothek von Platzhaltern)
# ---------------------------------------------------------------------------
class BildSymbol(models.Model):
    """Eine Bibliothek an Symbol-Platzhalterbildern.

    ``pfad`` ist relativ und zeigt in ``MEDIA_ROOT/BILD-symbol-root``.
    """

    bezeichnung = models.CharField(max_length=120, unique=True)
    pfad = models.CharField(max_length=255, help_text="Relativ zu settings.FLOHMARKT_MEDIA_ROOT.")
    beschreibung = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["bezeichnung"]
        verbose_name = "Symbolbild"
        verbose_name_plural = "Symbolbilder"

    def __str__(self) -> str:
        return self.bezeichnung

    @property
    def abs_pfad(self) -> Path:
        return Path(django_settings.MEDIA_ROOT) / django_settings.FLOHMARKT_SYMBOL_ROOT / Path(self.pfad).name


# ---------------------------------------------------------------------------
# Bild (pro Artikel, mit source: upload | symbol)
# ---------------------------------------------------------------------------
class Bild(models.Model):
    artikel = models.ForeignKey(Artikel, on_delete=models.CASCADE, related_name="bilder")

    source = models.CharField(
        max_length=10,
        choices=BildSource.choices,
        default=BildSource.UPLOAD,
    )

    # Entweder ein eigenes Pfad (upload),
    pfad = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Relativ zu settings.FLOHMARKT_IMAGE_ROOT (nur bei source=upload).",
    )

    # oder ein Bezug auf ein Symbolbild (source=symbol)
    symbol = models.ForeignKey(
        BildSymbol,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="verwendungen",
    )

    alt_text = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0, help_text="Reihenfolge im Artikel.")
    is_primary = models.BooleanField(default=False, help_text="Cover-/Primärbild des Artikels.")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "id"]
        verbose_name = "Bild"
        verbose_name_plural = "Bilder"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(source=BildSource.UPLOAD, pfad__isnull=False, symbol__isnull=True)
                    | models.Q(source=BildSource.SYMBOL, pfad__isnull=True, symbol__isnull=False)
                ),
                name="bild_source_exklusiv",
            )
        ]

    def __str__(self) -> str:
        return f"Bild {self.pk} [{self.source}] für {self.artikel_id}"

    @property
    def abs_pfad(self) -> Path | None:
        if self.source == BildSource.SYMBOL:
            return self.symbol.abs_pfad if self.symbol else None
        if not self.pfad:
            return None
        return Path(django_settings.MEDIA_ROOT) / django_settings.FLOHMARKT_IMAGE_ROOT / Path(self.pfad).name


# ---------------------------------------------------------------------------
# Plattformstatus — NxM Artikel × Plattform
# ---------------------------------------------------------------------------
class PlatformStatus(models.Model):
    """Status eines Artikels auf einer bestimmten Plattform.

    Später erweiterbar:
      - ``preis_override`` (Decimal, nullable): eigener Preis/Netto-Einkauf auf
        genau dieser Plattform (z. B. wegen Gebühren-/Porto-Modell).
      - ``pp_override`` (FK → PPOption, nullable): andere P&P-Option als der
        Artikelbasis.
    """

    artikel = models.ForeignKey(Artikel, on_delete=models.CASCADE, related_name="plattformstatus_set")
    platform = models.ForeignKey(Plattform, on_delete=models.CASCADE, related_name="status_set")

    status = models.CharField(
        max_length=20,
        choices=PlattformStatusStatus.choices,
        default=PlattformStatusStatus.INAKTIV,
    )
    externe_id = models.CharField(max_length=255, blank=True, null=True)
    letzte_fehlermeldung = models.TextField(blank=True)
    letzte_sync = models.DateTimeField(blank=True, null=True)

    # --- Spätere Erweiterungen (offen, noch nicht als Datenbank-Spalte) -------
    # preis_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # pp_override = models.ForeignKey(PPOption, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["artikel", "platform"], name="ein_status_pro_artikel_platform"),
        ]
        ordering = ["artikel", "platform"]
        verbose_name = "Plattformstatus"
        verbose_name_plural = "Plattformstatus"

    def __str__(self) -> str:
        return f"{self.artikel} → {self.platform}: {self.status}"

    @property
    def effective_preis(self) -> Decimal | None:
        return self.artikel.preis  # V1: kein Override.

    def mark_sync(self, ok: bool, msg: str = "") -> None:
        self.letzte_sync = timezone.now()
        if ok:
            self.status = PlattformStatusStatus.AKTIV
            self.letzte_fehlermeldung = ""
        else:
            self.status = PlattformStatusStatus.FEHLGESCHLAGEN
            self.letzte_fehlermeldung = msg
        self.save(update_fields=["letzte_sync", "status", "letzte_fehlermeldung", "updated_at"])
