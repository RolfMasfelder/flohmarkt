"""pytest-Config für die Suite: Fixtures (DB, Client, Basisdaten)."""

from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from project.core.models import Artikel, Plattform, PPOption


@pytest.fixture
def user(db) -> User:
    return User.objects.create_superuser("test_user", "test@local.test", "kein-Klartext-pflicht")


@pytest.fixture
def api_client(user) -> APIClient:
    """Authentifizierter DRF-Client (force_authenticate — kein Passwort-Hash nötig)."""
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def default_pp(db) -> PPOption:
    """Die 0-€-Selbstabhol-Option (genau eine ist als Default markiert)."""
    PPOption.objects.update(is_default=False)
    obj, _ = PPOption.objects.get_or_create(
        bezeichnung="Selbstabholung",
        defaults={"kosten": Decimal("0.00")},
    )
    obj.is_default = True
    obj.save(update_fields=["is_default"])
    return obj


@pytest.fixture
def plat_kleinanzeigen(db) -> Plattform:
    obj, _ = Plattform.objects.get_or_create(
        name="Kleinanzeigen",
        defaults={"adapter_slug": "kleinanzeigen", "is_aktiv": True, "konfiguration": {}},
    )
    return obj


@pytest.fixture
def artikel(default_pp, db) -> Artikel:
    return Artikel.objects.create(
        titel="Vintage-Teller (Minitest)",
        beschreibung="Ein sauberer Minitest-Artikel.",
        preis=Decimal("42.90"),
        anzahl_verfügbar=3,
    )
