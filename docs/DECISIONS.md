# DECISIONS.md — Architecture Decision Records (ADRs)

Format: ADR-NN · Kurz · Status (akzeptiert/verworfen/nicht-kraft) · Kontext ·
Entscheidung · Konsequenzen. Nur **stabilisierte** Entscheidungen landen hier —
detailliertere Begründung in `docs/arc42.md`.

---

## ADR-01 · Ein Preis pro Artikel, nicht pro Plattform

- **Status:** akzeptiert (2026-11-20)
- **Kontext:** Artikelpreis auf Kleinanzeigen vs. ebay unterscheiden sich oft
  (Fees). Komplexität pro-Plattform-Preis wäre groß (Synchronisation,
  Abweichungs-Tracking).
- **Entscheidung:** `Artikel.preis` ist der **einzige** Preis pro Artikel.
  Plattformgebühren werden v1 nicht modelliert.
- **Konsequenzen:**
  - Einfache UI (ein Feld), keine Feels-Logik pro Plattform.
  - Preis-Ableitung aus Gebühren (z.B. „+15 % eBay") ist ein laterales Feature
    (Adapter-Rechungsmodell) — v1 aus.
  - **Expansion-Pfad:** Spätere `PlatformStatus.preis_override` (nullable)
    ermöglicht Abweichung pro Plattform ohne Schema-Break.

## ADR-02 · PPOption als eigene Tabelle

- **Status:** akzeptiert (2026-11-20)
- **Kontext:** P&P-Preis (0 € = Selbstabholung) ist eine **feste** Wahl (z.B.
  „3 € versichert", „5 € DHL") und gilt für den Artikel, nicht nur für eine
  Plattform. Echte Variante in 2 Feldern (`pp_preis`, `pp_beschreibung`) wäre
  zu stumm; 2 Tabellen wären überdimensioniert.
- **Entscheidung:** `PPOption` = 1:1 FK vom Artikel (Default: neue Option wird
  angelegt). `preis` default 0.00 € (Selbstabholung).
- **Konsequenzen:**
  - Artikel ohne PPOption (Self-Pickup) ist trivial: 0 €-Option.
  - Neue PPOptionen (z.B. „Nachnahme") sind Daten, keine Migration.
  - 1:1 ist **logisch**, nicht physisch — keine DB-Vollständigkeit-Notwendigkeit.

## ADR-03 · Adapter-Layer für Plattformen (Kleinanzeigen v1)

- **Status:** akzeptiert (2026-11-21)
- **Kontext:** Kleinanzeigen hat **keine offizielle öffentliche API**;
  `api.kleinanzeigen.de` ist die interne App-API (CORS-Bypass, Sessions).
  Offizielle API-Referenz: keine. Unofficial: `monkrel/kleinanzeigen-api`
  (Python, inaktiver Stand — **Nicht** als Dependency).
- **Entscheidung:** `core/adapters/base.py` mit `Protocol`/ABC;
  `core/adapter_registry.py` mit slug→Impl-Karte; Kleinanzeigen-Adapter v1.
  **Kein** Hardcoding in ViewSets — jeder API-Call geht durch den Adapter.
- **Konsequenzen:**
  - Breaking-Change in der Plattform-API ⇒ nur 1 Datei zu patchen, Backends
    und Frontend bleiben stabil.
  - Rate-Limits/Backoff sind Adapter-Kompetenz (nicht in der Web-App).
  - Feature-Flags via `Adapter.slug`-Präsenz in `core/adapter_registry.py`
    (deaktivierter Adapter = kein Eintrag in der Registry).

## ADR-04 · Kein Build-Step für das Frontend

- **Status:** akzeptiert (2026-11-21), ab 2026-11-20
- **Kontext:** Firefox-First (kein `node_modules`-Build-Step). Performance < 5k
  Artikel. Kein CDN-Notwendigkeit v1. WhiteNoise genügt.
- **Entscheidung:** Django Templates + HTMX + Vanilla JS. HTMX via CDN
  (kein Local-Package). Keine SPA, kein `npm`.
- **Konsequenzen:**
  - `Dockerfile` bleibt schlank (kein Node-Layer).
  - UI-Komplexität begrenzt (HTMX-Events, keine React-Virtualisierung).
  - Für größere Features (Drag&Drop, Live-Search) später:
    `django-cotton` oder HTMX-Alternative (z.B. `htmx-boosted`) — ADR-erforderlich.

## ADR-05 · Settings-Leiter: base + {development, production, testing}

- **Status:** akzeptiert (2026-11-21)
- **Kontext:** `FLOHMARKT_PROFILE` steuert das Settings-Modul;
  `testing` = SQLite-by-Default (kein Postgres in CI-Pipeline für Unit-Tests),
  `production` = fail-fast (`SystemExit` bei fehlenden Secrets).
- **Entscheidung:** `project.settings.{base,development,production,testing}`.
  `DJANGO_SETTINGS_MODULE` aus Env (`FLOHMARKT_PROFILE`).
- **Konsequenzen:**
  - `pyproject.toml`: `DJANGO_SETTINGS_MODULE = "project.settings.testing"`
    als Default (pytest).
  - Production: `ALLOWED_HOSTS`, `SECRET_KEY`, `POSTGRES_*` — alle hart.
  - Keine `.env` im Repo — `.env.example` + `.env.ci` als Referenz.

## ADR-06 · Python 3.14 / Django 6.1

- **Status:** akzeptiert (2026-11-19), Version check 2026-11-21
- **Kontext:** Aktiver Support bis ~2027 (3.14 bis 2028+).
  Django 6.1.x ist aktives Non-LTS (LTS = 6.2, ab 2027-04).
- **Entscheidung:** `requires-python >=3.14,<3.15` in `pyproject.toml`;
  `Django >=6.1,<6.2`. Django 6.2 LTS als Upgrade-Pfad (2027-04).
- **Konsequenzen:**
  - `ruff` mit `target-version = "py314"`.
  - Kein `from django.utils import deprecation` — `RemovedInDjango*`-Warnings
    werden gefixt.
  - `pytest-django >=4.11`.
