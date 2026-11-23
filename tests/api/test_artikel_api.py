"""API-Tests: DRF-Endpoints, Auth, Filter, OpenAPI-Schema."""

import pytest

pytestmark = pytest.mark.django_db


def test_api_fordert_authentication(db, rf):
    """Ohne Auth → 401 (IsAuthenticated ist Default)."""
    from rest_framework.test import APIClient

    c = APIClient()
    resp = c.get("/api/artikel/")
    # 401 (Basic/Token) bzw. 403 (Session+CSRF-Verweigerung) — beides "nicht drin"
    assert resp.status_code in (401, 403)


def test_api_schema_reachbar(api_client):
    resp = api_client.get("/api/schema/")
    assert resp.status_code == 200


def test_api_artikel_liste(api_client, artikel, default_pp, plat_kleinanzeigen):
    resp = api_client.get("/api/artikel/")
    assert resp.status_code == 200
    body = resp.json()
    results = body["results"] if isinstance(body, dict) and "results" in body else body
    assert artikel.id in [a["id"] for a in results]


def test_api_artikel_detail(api_client, artikel):
    r = api_client.get(f"/api/artikel/{artikel.id}/")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == artikel.id
    assert body["rest_verfügbar"] == 3
    assert body["pp_bezeichnung"] == "Selbstabholung"


def test_api_ppoptionen(api_client, default_pp):
    resp = api_client.get("/api/pp-options/")
    assert resp.status_code == 200
    body = resp.json()
    ids = [e["id"] for e in (body["results"] if isinstance(body, dict) else body)]
    assert default_pp.id in ids


def test_api_plattformen(api_client, plat_kleinanzeigen):
    resp = api_client.get("/api/plattformen/")
    assert resp.status_code == 200
    body = resp.json()
    names = [p["name"] for p in (body["results"] if isinstance(body, dict) else body)]
    assert "Kleinanzeigen" in names


def test_api_verkauft_filter(api_client):
    """?verkauft=true liefert nur verkaufte Artikel."""
    from decimal import Decimal

    from project.core.models import Artikel

    v = Artikel.objects.create(
        titel="Kauf-Abteil",
        beschreibung="x",
        preis=Decimal("1.00"),
        anzahl_verfügbar=1,
        anzahl_verkauft=1,
        verkauft=True,
    )
    off = Artikel.objects.create(
        titel="Noch da",
        beschreibung="y",
        preis=Decimal("1.00"),
    )

    alle = api_client.get("/api/artikel/").json()["results"]
    ids = {a["id"] for a in alle}
    assert v.id in ids and off.id in ids

    resp_v = api_client.get("/api/artikel/?verkauft=true")
    ids_v = {a["id"] for a in resp_v.json()["results"]}
    assert v.id in ids_v and off.id not in ids_v

    resp_o = api_client.get("/api/artikel/?verkauft=false")
    assert off.id in {a["id"] for a in resp_o.json()["results"]}
