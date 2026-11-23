"""Integrationstests: laufen ideal gegen PostgreSQL (``make pytest-docker``).

Dekoriert mit ``pytest.mark.integration`` — separat markiert, damit die
Schnell-Suite sie optional ausblenden kann (``-m "not integration"``).

Abgedeckt:
- ``/api/healthz/`` — Liveness ohne Auth + ohne DB-Zugriff.
- ``seed_basics`` — Idempotenz (mehrfache Ausführung sicher, genau ein Default).
- E2E-Artikel-Lebenszyklus über die API inkl. abgeleiteter Felder.
- ``PlatformStatus``-UniqueConstraint (ein Status pro Artikel und Plattform).
"""

from decimal import Decimal

import pytest
from django.core.management import call_command
from django.db import IntegrityError, transaction

from project.core.models import PlatformStatus, PPOption, Zustand

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_healthz_ohne_auth_und_db(client):
    """Liveness-Check: kein Auth, 200 + {"status": "ok"} — auch ohne jede Fixture."""
    resp = client.get("/api/healthz/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_seed_basics_idempotent(db):
    """Zweimal ausführen: keine Duplikate, genau ein Default, drei P&P-Optionen."""
    call_command("seed_basics")
    call_command("seed_basics")  # zweites Mal muss idempotent bleiben

    assert PPOption.objects.filter(bezeichnung="Selbstabholung").count() == 1
    assert PPOption.objects.filter(bezeichnung="Paket").count() == 1
    assert PPOption.objects.filter(bezeichnung="Maxi-Paket").count() == 1

    # Genau eine Option trägt das Default-Flag…
    defaults = PPOption.objects.filter(is_default=True)
    assert defaults.count() == 1
    # …und das ist die 0-€-Selbstabholung.
    assert defaults.first().bezeichnung == "Selbstabholung"
    assert defaults.first().kosten == Decimal("0.00")


def test_artikel_lebenszyklus_e2e(api_client, default_pp, plat_kleinanzeigen):
    """Create → Read → abgeleitete Felder → Plattformstatus → Read.

    Glatte Fahrt über die API inkl. der Read-Only-Felder ``rest_verfügbar``
    und ``pp_bezeichnung``, die der Serializer aus dem Modell ableitet.
    """
    # -- Create -------------------------------------------------------------
    resp = api_client.post(
        "/api/artikel/",
        {
            "titel": "E2E-Test-Artikel",
            "beschreibung": "Vollständiger Lauf durch die API.",
            "preis": "99.90",
            "pp_option": default_pp.id,
            "zustand": Zustand.NEU,
            "anzahl_verfügbar": 2,
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    artikel_id = resp.json()["id"]

    # -- Read (Detail) mit abgeleiteten Feldern ------------------------------
    detail = api_client.get(f"/api/artikel/{artikel_id}/").json()
    assert detail["titel"] == "E2E-Test-Artikel"
    assert detail["rest_verfügbar"] == 2
    assert detail["verkauft"] is False
    assert detail["pp_bezeichnung"] == "Selbstabholung"
    assert Decimal(str(detail["pp_kosten"])) == Decimal("0.00")

    # -- Plattformstatus anlegen (Unique: ein Status pro Artikel und Plattform)
    PlatformStatus.objects.create(
        artikel_id=artikel_id,
        platform=plat_kleinanzeigen,
        status="aktiv",
    )

    detail = api_client.get(f"/api/artikel/{artikel_id}/").json()
    assert len(detail["plattformstatus"]) == 1
    assert detail["plattformstatus"][0]["platform_name"] == "Kleinanzeigen"

    # -- Zweiter Status auf gleicher Plattform muss Unique-Constraint brechen
    with pytest.raises(IntegrityError), transaction.atomic():
        PlatformStatus.objects.create(
            artikel_id=artikel_id,
            platform=plat_kleinanzeigen,
            status="gesperrt",
        )
