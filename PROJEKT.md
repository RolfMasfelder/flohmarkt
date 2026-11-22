# PROJEKT.md — flohmarkt

> Verwaltung von Handelsartikeln, die auf mehreren Plattformen (Kleinanzeigen u. a.) angeboten werden.
> Status: **v1 implementiert & verifiziert** — Docker-Stack + PG 18 live, 18/18 Tests (lokal + Postgres), auf `dev` gepusht (Stand: 2026-11-22)
> Doku-Quellen: `PROJEKT.md` (dies), `docs/arc42.md`, `docs/DECISIONS.md` (ADRs)

## 1. Ziel

- Artikel zentral anlegen und verwalten (Eigennutz, kein kommerzieller Vertrieb).
- Mehrere Plattformen **konfigurierbar** anbinden (Plugin/Adapter-Schicht, nie hartkodiert).
- Lokal nutzbar (Docker Compose), aber public-GitHub-repo-tauglich: saubere Config-Trennung, Security-Defaults.

## 2. Entscheidungen (Stack) — Versionen am 2026-11-19/21 geprüft

| Bereich | Wahl | Version/Hinweis |
|---|---|---|
| Sprache | Python | **3.14** (aktiver Support; 3.13 ist seit 10/2026 nur Security-Support) |
| Backend | Django | **6.1.3** (aktuell; 6.2 LTS ab 04/2027) |
| REST | djangorestframework | 3.18.x (aktuell) |
| OpenAPI | drf-spectacular | 0.30.x (< 1.0 by design → strikt pinnen, Schema-Diff bei Updates) |
| DB | PostgreSQL | **18** (via docker image) |
| DB-Client (Py) | psycopg 3 | 3.3.x, async-fähig |
| HTTP (Adapter-Client) | httpx | async/modern |
| Frontend | **HTMX + Django-Templates** | läuft in gängigen Browsern (Firefox-First), **kein Build-Step** (ADR-04) |
| Config | env-Variablen | Secrets **nie** in git; nur `.env.example` im Repo |
| Tests | pytest + pytest-django | Unit: SQLite · Integration: Postgres (Compose/CI) |
| Doku | arc42 + ADRs | `docs/arc42.md`, `docs/DECISIONS.md` |
| SBOM | cyclonedx via `syft` | im CI-Workflow |

**Entscheidung: kein FastAPI** — DRF + drf-spectacular deckt REST + OpenAPI ab. Kein Build-Step. Kein `npm`.

## 3. Datenmodell v1 (2026-11-20, mit Rolf besprochen)

**Festgelegt:**
- **Ein Preis pro Artikel** (`artikel.preis`) — ADR-01.
- **P&P als eigene Tabelle** (`PPOption`), 1:1-FK vom Artikel — ADR-02.
- Spätere Erweiterungspunkt: `PlatformStatus.preis_override` (Decimal, nullable) + `Boolean` — ohne Schema-Break.

*(Tabelle-Details + Migrationen: `src/project/core/migrations/0001_initial.py`.)*

| Modell | Haupt-Felder | Relation |
|---|---|---|
| `Artikel` | `titel`, `beschreibung`, `kategorie?`, `zustand`, `preis`, `pp_option`, `verkauft`, `created/updated` | N→1 Kategorie · N→1 PPOption |
| `PPOption` | `bezeichnung`, `kosten`, `beschreibung?`, `is_default` (Default 0€) | 1→1 Artikel |
| `Kategorie` | `name` (unique), `parent?` (hierarchisch) | 1→N Artikel |
| `Bild` | `artikel`, `pfad`, `alt_text?`, `position`, `is_primary` | N→1 Artikel |
| `BildSymbol` | (symbol-basierte Bilder) | N→1 Bild |
| `PlatformStatus` | `status`, `externe_id?`, `letzte_fehlermeldung?`, `created/updated` + UniqueConstraint(artikel, plattform) | N→1 Artikel · N→1 Plattform |
| `Plattform` | `name`, `adapter_slug`, `konfiguration` (JSONB), `is_aktiv` | 1→N PlatformStatus |

## 4. Architektur

```txt
┌───────────────────────────────────────────┐
│ UI: Django Templates + HTMX (Firefox-First) │
├───────────────────────────────────────────┤
│ Django 6.1: Settings-Leiter (dev/prod/testing) │
│    Views (HTMX), Admin, Forms, DRF-ViewSets  │
├───────────────────────────────────────────┤
│ Adapter-Layer:                             │
│    core/adapters/base.py  (Protocol/ABC)   │
│    core/adapter_registry.py (slug→Impl)    │
│    core/adapters/kleinanzeigen.py (v1, unoffiziell) │
├───────────────────────────────────────────┤
│ PostgreSQL 18 · static/ (WhiteNoise) · media/ │
└───────────────────────────────────────────┘
```

- **NxM-Relation** `Artikel × Plattform` via `PlatformStatus` (ADR-03).
- **Adapter-Interface** ist die zentrale Designentscheidung: Domäne kennt nur `Item`/`PlatformStatus`.
- **Kleinanzeigen-Adapter v1**: `api.kleinanzeigen.de` (interne App-API). Referenz: `monkrel/kleinanzeigen-api` (inaktiv, **nicht** als Dependency). Risiko: Breaking-Changes → ADR-03.

## 5. Security / Zero-Trust (lokale Instanz, aber public-repo)

- Lokale Installation, aktuell keine externen Nutzenden.
- Public-repo ⇒ Zero-Trust-Basis:
  - **HTTPS** mit LetsEncrypt (Caddy/Traefik als Front? offen)
  - Secrets nur via env, `FLOHMARKT_PROFILE=production` **fail-fast** (ADR-05)
  - `.gitignore`: echte `.env`; Repo bekommt nur `.env.example`
  - Rate-Limiting, CORS-Defaults, HSTS in `production.py`

## 6. Workflow / Toolchain

- **Docker Compose** als Basis (python:3.14-slim, PostgreSQL 18)
- Entwicklung: `dev` → push → **GitHub PR → main** (branch rules: no direct push; Dependabot Auto-Merge nur für Minors)
- CI (`.github/workflows/ci.yml`): `lint` (ruff) → `test-sqlite` (unit) → `test-postgres` (integration) → `SBOM` (syft → cyclonedx-json) → `build GHCR`
- `Makefile`: `help/venv/check/migrate/pytest/lint/up/logs/pytest-docker/schema/clean`

## 7. Open / noch zu klären

- [x] Datenmodell konkret: Artikel-Attribute, Kategorie, Zustand, Bilder, Preis (→ §3)
- [x] arc42-Doku + ADRs (→ `docs/arc42.md`, `docs/DECISIONS.md`)
- [ ] GitHub branch rules: noch zu konfigurieren (main-Protect, Dependabot Auto-Merge)
- [ ] Letsencrypt-Setup: Caddy oder Traefik?
- [ ] Zahlungs-logik: v1 keine Plattform-Gebühren-Modellierung
- [ ] E2E-Tests: Playwright (nach HTMX-Basistests stabil)
- [ ] SBOM-Veröffentlichung/GHCR-Paket-Artifakt: nach PR

## 8. Repo-Layout (v0)

```
flohmarkt/
├── docs/arc42.md
├── docs/DECISIONS.md
├── PROJEKT.md
├── .env.example
├── .github/workflows/ci.yml
├── .gitignore
├── Dockerfile
├── Makefile
├── docker-compose.yml
├── manage.py
├── pyproject.toml
├── ruff.toml
├── venv/
├── src/project/
│   ├── settings/{base,development,production,testing}.py
│   ├── core/
│   │   ├── adapters/{base,registry,kleinanzeigen}.py
│   │   ├── migrations/0001_initial.py
│   │   ├── admin.py · apps.py · forms.py · management/seed_basics.py
│   │   ├── models.py · urls.py · views.py
│   │   └── templates/…
│   ├── api/{apps,serializers,urls,views}.py
│   ├── templates/
│   ├── wsgi.py · asgi.py · urls.py
└── tests/{unit,api,integration}/
```
