# PROJEKT.md — flohmarkt

> Verwaltung von Handelsartikeln, die auf mehreren Plattformen (Kleinanzeigen u. a.) angeboten werden.
> Status: Entwurf / In-Arbeit-nahme (Stand: 2026-11-19, mit Rolf besprochen)

## 1. Ziel

- Artikel zentral anlegen und verwalten (Eigennutz, kein kommerzieller Vertrieb).
- Mehrere Plattformen **konfigurierbar** anbinden (Plugin/Adapter-Schicht, nie hartkodiert).
- Lokal nutzbar (Docker Compose), aber public-GitHub-repo-tauglich: saubere Config-Trennung, Security-Defaults.

## 2. Entscheidungen (Stack) — Versionen am 2026-11-19 geprüft

| Bereich | Wahl | Version/Hinweis |
|---|---|---|
| Sprache | Python | **3.14** (aktiver Support; 3.13 ist seit 10/2026 nur Security-Support) |
| Backend | Django | **6.1.3** (aktuell; 6.2 LTS ab 04/2027) |
| REST | djangorestframework | aktuell pinnen, pinning erzwingen |
| OpenAPI | drf-spectacular | <1.0 by design → strikt pinnen, Schema-Diff bei Updates |
| DB | PostgreSQL | 18 (via docker image) |
| HTTP (Adapter-Client) | httpx | async/modern |
| Frontend | **HTMX + Django-Templates** | läuft in gängigen Browsern (Firefox-First), keine Build-Chain |
| Config | env-Dateien + config.json | Secrets **nie** in git; nur `.env.example` / `config.json.example` kommentiert |
| Validation | Pydantic v2 | **optional**, für Plattform-Schemata in der Adapter-Schicht |
| Tests | pytest | vom ersten Commit an: hohe Abdeckung, Integrations- + E2E-Tests |
| Doku | arc42 | schlank, nicht akademisch; dazu `docs/DECISIONS.md` (ADRs, ~5 Zeilen/Entscheid) |
| SBOM | cyclonedx via `syft` | im CI-Workflow (Depends + Container-Scans) |

Entscheidung: **kein FastAPI** neben Django (doppelter Wartungsstapel). DRF + drf-spectacular deckt REST + OpenAPI ab.

## 3. Architektur (entwurf)

```txt
┌───────────────────────────────────────────┐
│ UI: Django Templates + HTMX (Firefox-tauglich) │
├───────────────────────────────────────────┤
│ Django 6.1: Views, Admin (Systemtabellen, │
│ User, Plattform-Konfiguration), DRF-API   │
├───────────────────────────────────────────┤
│ Domäne: Artikel, Plattform-Lokal-Status,   │
│ NxM-Relation Artikel×Plattform (aktiv/inaktiv/…) │
├───────────────────────────────────────────┤
│ Adapter-Layer (Plugin, dynamische Load):  │
│ base: create/update/delete/sync, Status   │
│ kleinanzeigen.py (v1, unoffiziell API)    │
│ (weitere: ebay, sub24 … später)           │
├───────────────────────────────────────────┤
│ Config: env (Secrets), config.json (rest) │
└───────────────────────────────────────────┘
```

- **NxM-Relation**: `Artikel <→ Plattform`: Status (aktiv/inaktiv), externe ID, letzte Sync, Fehler.
- **Adapter-Interface** ist die zentrale Designentscheidung: Domäne kennt nur `Item`/`PlatformStatus`, nie ein konkretes Framework.
- **Kleinanzeigen-Adapter v1**: kein public API → interne `api.kleinanzeigen.de` (App-API) + ggf. Unofficial-Client als Referenz. Risiko: unoffizielle APIs brechen können (→ arc42-Risiken).

## 4. Security / Zero-Trust (lokale Instanz, aber public-repo)

- Lokale Installation, aktuell keine externen Nutzenden.
- Trotzdem: public-repo ⇒ muss jemand auch aus dem externen Netz betreiben können → Zero-Trust-Basis:
  - **HTTPS** mit LetsEncrypt (Caddy/Traefik als Front? offen)
  - Secrets nur via env, nie hartkodiert, nie in git
  - `.gitignore`: echte `.env`, `config.json`; repo bekommt `.env.example`, `config.json.example`
  - Rate-Limiting, CORS-Defaults, sichere Django-Settings-Profile (dev/prod)

## 5. Workflow / Toolchain

- **Docker Compose** als Basis (Python 3.14, PostgreSQL, ggf. Caddy)
- Entwicklung: `dev` → push → **GitHub PR → main** (branch rules: kein direct push, Checks grün, nur dependabot PRs = Auto-Merge)

### github-branch-Verhalten (noch zu konfigurieren)

- `main`: Protected — kein Direct Push.
- PRs von dependabot: auto-merge nach grünen Checks.
- PRs von Rolf/anderen: require review, kein auto-merge.
- `.github/workflows`: checks (lint, format, pytest, SBOM-Scan via syft+cyclonedx)
- **Dependabot**: aktiviert, auto-merge für deps

## 5.5 Datenmodell v1 (2026-11-20, mit Rolf besprochen)

**Festgelegt:**
- **Ein Preis pro Artikel** (`artikel.preis`), kein Preis pro Plattform. Gebührenstruktur noch unklar.
- **P&P als eigene Tabelle** (`PPOption`) mit FK vom Artikel; Default-Option 0 € = Selbstabholung.
- Spätere Erweiterungspunkt: `PlatformStatus.preis_override` (Decimal, nullable) + `Boolean` — ohne Migration an `Artikel`.

### `Artikel`
| Attribut | Typ | Notizen |
|---|---|---|
| `id` | `BigInt` (PK, auto) | |
| `titel` | `Char(150)` | Pflicht; Adapter darf kürzen (Kleinanzeigen ~40 Zeichen) |
| `beschreibung` | `Text` | |
| `kategorie` | `FK → Kategorie` (nullable) | optional |
| `zustand` | `Char(20)` choices: neu / gebraucht / defekt_funktional / defekt | |
| `preis` | `Decimal(10,2)` | ein fester Preis pro Artikel |
| `pp_option` | `FK → PPOption` | Pflicht; Default = 0-€-Option (Selbstabholung) |
| `verkauft` | `Boolean` | Default False |
| `created_at` / `updated_at` | `DateTime` | auto |

### `PPOption`
| Attribut | Typ | Notizen |
|---|---|---|
| `id` | `BigInt` (PK) | |
| `bezeichnung` | `Char(120)` | z. B. „Versand per Paket" |
| `kosten` | `Decimal(10,2)` | |
| `beschreibung` | `Text` (nullable) | |
| `is_default` | `Boolean` | exakt eine = True (DB-Level/Constraint) |

Seed: „Abholung (0 €)" = Default, dazu sinnvolle Versand-Optionen (Beträge frei, via seed-Command).

### `Kategorie`
| Attribut | Typ | Notizen |
|---|---|---|
| `id` | `BigInt` (PK) | |
| `name` | `Char(100)` | unique |
| `parent` | `FK → Kategorie` (nullable) | optional hierarchisch |

### `Bild`
| Attribut | Typ | Notizen |
|---|---|---|
| `id` | `BigInt` (PK) | |
| `artikel` | `FK → Artikel` (CASCADE) | |
| `pfad` | `Char(255)` | relativer Pfad `bilder/…` |
| `alt_text` | `Char(255)` (nullable) | |
| `position` | `Int` | |
| `is_primary` | `Boolean` | |

### `PlatformStatus` (NxM Artikel × Plattform)
| Attribut | Typ | Notizen |
|---|---|---|
| `id` | `BigInt` (PK) | |
| `artikel` | `FK → Artikel` (CASCADE) | |
| `plattform` | `FK → Plattform` | |
| `status` | `Char(20)` choices: aktiv / inaktiv / gesperrt / fehlgeschlagen | |
| `externe_id` | `Char(255)` (nullable) | |
| `letzte_fehlermeldung` | `Text` (nullable) | |
| `created_at` / `updated_at` | `DateTime` | |

### `Plattform`
| Attribut | Typ | Notizen |
|---|---|---|
| `id` | `BigInt` (PK) | |
| `name` | `Char(50)` | |
| `adapter_slug` | `Char(50)` | python Modul/Plugin der die Plattform bedient |
| `konfiguration` | `JSONB` | plattform-spezifisch (URLs, Zeitversatz, …) |
| `is_aktiv` | `Boolean` | |

## 6. Open / noch zu klären

- [x] Datenmodell konkret: Artikel-Attribute, Kategorie, Zustand, Bilder, Preis (→ 5.5)
- [ ] Zahlungs-logkik: rein admin (Plattform zahlt) oder Tracking? → V1: nein
- [ ] Letsencrypt-Setup: Caddy oder Traefik?
- [ ] GitHub branch rules: noch zu konfig
- [ ] arc42-Doku: nach Datenmodell
