# arc42 — flohmarkt (schlank)

> Version: 1.0 · Stand: 2026-11-21 · Autor: Rolf + Selma
> Prinzip: schlank, praxisbezogen — keine akademische Füllung.

## 1. Zielsetzung

Zentrale Verwaltung von Handelsartikeln, die auf mehreren Plattformen
(Kleinanzeigen, später evtl. ebay/sub24) gleichzeitig angeboten werden.

- Eigenverwendung, kein kommerzieller Vertrieb.
- Lokal betrieben (Docker Compose), aber als **öffentliches GitHub-Repo** tauglich.
- Artikel **einmal** pflegen, Plattform-Status separat tracken (NxM).

**Nicht-Ziele (v1):** Zahlungs-/Buchhaltungstracking, Multiuser-RLS,
natürlichsprachliche Artikelerkennung, mobile Native-App.

## 2. Randbedingungen

- Public Repo ⇒ Zero-Trust-Basis: Secrets nur via Env, nie in git.
- Python 3.14 (aktiver Support bis 2028+), lokale Distro hat 3.13/3.14.
- Browser-Kompatibilität: Firefox-First → **kein Build-Step** für das Frontend
  (HTMX + Templates, nicht SPA).
- Performance: < 5k Artikel, < 10k Bilder erwartet → keine Cluster-DB, kein CDN nötig.
- Wartung: ein Mensch (Rolf) + Assistentin (Selma). Kein SLO-Druck.

## 3. Fachliches Szenario

- Rolf fotografiert einen Teller, legt ihn an (Titel, Beschreibung,
  Kategorie optional, Zustand, Preis, P&P-Option, Bilder).
- Artikel erscheint in der Liste; Detailseite zeigt Bilder, Status je Plattform.
- Adapter (Kleinanzeigen v1) synchronisiert Status, holt `externe_id`.
- Artikel kann „verkaufte" Flag pro Plattform (und global) bekommen.
- Verwaltung primär über Web-UI (HTMX), sekundär über REST-API.

## 4. Lösungsüberblick

```
┌──────────────────────────────────────────────────────┐
│  Browser: Django Templates + HTMX (CDN, kein Build)  │
├──────────────────────────────────────────────────────┤
│  Django 6.1 (Gunicorn, WhiteNoise)                   │
│    - core : Models, Views, Admin, Forms, Adapter-Reg.│
│    - api  : DRF-ViewSets + serializes + spectacular  │
│    - wsgi/asgi, settings/{base,dev,prod,testing}     │
├──────────────────────────────────────────────────────┤
│  Adapter-Layer:                                      │
│    core/adapters/base.py   (Protocol + ABC)          │
│    core/adapter_registry.py (Registry, slug→Impl)    │
│    core/adapters/kleinanzeigen.py  (v1, unoffiziell) │
├──────────────────────────────────────────────────────┤
│  PostgreSQL 18 · static/ (WhiteNoise) · media/       │
└──────────────────────────────────────────────────────┘
```

**Kern-Entscheidungen (Details in `docs/DECISIONS.md`):**
1. Django statt Fastapi/Flask — Admin, ORM, Template-Engine in einem Wartungsstapel.
2. **Kein** Preis pro Plattform — ein fester Preis pro Artikel v1.
3. `PPOption` als eigene Tabelle (FK vom Artikel), Default 0 € = Selbstabholung.
4. `Bild.source ∈ {upload, symbol}` mit **DB-CheckConstraint** für Exclusivität.
5. `PlatformStatus` als NxM-Brücke, `UniqueConstraint(artikel+plattform)`.
6. Secrets/Profile via `FLOHMARKT_PROFILE` (dev/prod/testing); keine `.env` im Repo.
7. **Kein** Build-Step für Frontend → HTMX + Templates + WhiteNoise.
8. Tests: pytest + pytest-django; Unit gegen SQLite, Integration gegen Postgres (Compose/CI).

## 5. Bausteine

### 5.1 Apps

| App | Inhalt |
|---|---|
| `project.settings` | Settings-Leiter: `base` + `{development,production,testing}` |
| `project.core` | Modelle (7), Views (HTMX), Admin, Forms, Adapter-Registry, `seed`-Command |
| `project.api` | DRF-ViewSets für `Artikel`, `PPOption`, `Plattform`, `Kategorie`; spectacular-Schema |

### 5.2 Domänen-Modelle (Tabellen)

```
Artikel 1──0..n Bild
Artikel n──1  Kategorie (hierarchisch, parent-FK)
Artikel n──1  PPOption
Artikel 1──0..n PlatformStatus ◄──n──1 Plattform
Bild    n──1  BildSymbol
PlatformStatus n──1 Plattform
```

Details & Felder in `PROJEKT.md` §5.5 (ist der Single-Source-of-Truth
für Feld-Namen/-Typen). Migrations: `src/project/core/migrations/0001_initial.py`.

### 5.3 Adapter (Kleinanzeigen v1)

**Risiko: keine offizielle Plattform-API.** `api.kleinanzeigen.de` ist die
interne App-API (CORS-Bypass, Sessions, `X-CSRFToken`, `x-plz` Headers).
Unofficial-Client-Referenzen (z.B. `monkrel/kleinanzeigen-api`) als Design-Hilfe,
aber **nicht** als Dependency. Erwartet: Rate-Limits, Breaking-Changes ohne
Vorankündigung → Adapter kapselt das (Timeouts, Backoff, Fehler-Slots in
`PlatformStatus.letzte_fehlermeldung`, `mark_sync()`-Semantik).

## 6. Cross-Cutting Concerns

- **Secrets**: `FLOHMARKT_PROFILE` wählt das Settings-Profil.
  - `development`: Localhost-Defaults, SQLite erlaubt.
  - `testing`: SQLite (Default) oder Postgres via `POSTGRES_HOST`-Presence.
  - `production`: Harte Guards — `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`,
    `POSTGRES_HOST/DB/USER/PASSWORD` müssen gesetzt sein (sonst `SystemExit`).
- **HTTPS/HSTS**: `production.py` setzt `SECURE_PROXY_SSL_HEADER`, `HSTS`,
  `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`. Reverse-Proxy (Caddy/Traefik)
  liefert das Zertifikat.
- **Logging**: `INFO` auf Konsole, Struktur via Log-Handler; keine `print()`s.
- **CORS**: Default restriktiv (nur eigene Origin). API-Consumer via `CORS_ALLOWED_ORIGINS`.
- **Static**: WhiteNoise `CompressedStaticFilesStorage` (kein CDN-Notwendigkeit in v1).
- **Uploads**: `MEDIA_ROOT` aus Env; Dateigröße-Limit via `DATA_UPLOAD_MAX_MEMORY_SIZE`
  und Django-Upload-Begrenzung.
- **CSP/CSRF**: Django-Default + `X_FRAME_OPTIONS = DENY` in prod.

## 7. Risiken & offene Punkte

| Risiko | Impact | Mitigation |
|---|---|---|
| Kleinanzeigen-API breakt ohne Ankündigung | Adapter down | Backoff, Fehler-Slots in `PlatformStatus`, Adapter-Versionen + Feature-Flags per `adapter_slug`-Konfiguration |
| Public Repo + private Daten-Abuse | Datenexfiltration | `.env`-git-Ignore, `FLOHMARKT_PROFILE=production` fail-fast, keine `git push --force` auf main, `dependabot` nur `main` |
| Django 6.2 LTS (2027) | Migration | Versionspinning + `ruff`-Upgrade-Checks im CI; `RemovedInDjango2028*`-Warnings werden gefixt |
| Ein-Personen-Wartung | Bus-Faktor | Selma-Assistenz + ARC42 als Kontext + ADRs in `docs/DECISIONS.md` |
| Bilder-Dateisystem | Storage-Ausfall | `MEDIA_ROOT` als Volume; spätere S3-Option als Adapter (nicht v1) |

**Offen / zu konfigurieren:**
- GitHub branch rules (main-Protect, Dependabot Auto-Merge) — Repo-Seiten.
- Caddyfile/Traefik-Konfig + Let's Encrypt (v0.1 ohne TLS — lokal nur).
- E2E-Tests (Playwright) — nach HTMX-Basistests stabil.
- OpenAPI-Client-Generierung (python `drf-spectacular`-CLI → `python openapi-generator-cli`).
