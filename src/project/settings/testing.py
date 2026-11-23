"""Test-Profil: eigene DB, SQLite für Geschwindigkeit (Docker/CI nutzt Postgres im CI-Plan)."""

import os

from .base import *  # noqa: F403

# Test-Instanz
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Test-DB: Default SQLite (lokal/CI-light); mit POSTGRES_HOST auf einen
# erreichbaren Server gesetzt -> PostgreSQL (für Integrationstests, z.B. Compose).
if os.environ.get("POSTGRES_HOST"):
    DATABASES["default"].update(
        {
            "NAME": env.str("POSTGRES_DB", "flohmarkt_test"),
            "USER": env.str("POSTGRES_USER", "flohmarkt"),
            "PASSWORD": env.str("POSTGRES_PASSWORD", ""),
            "HOST": env.str("POSTGRES_HOST"),
            "PORT": env.str("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 0,
        }
    )
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db_test.sqlite3",
        }
    }

# Kein Spam bei Tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
