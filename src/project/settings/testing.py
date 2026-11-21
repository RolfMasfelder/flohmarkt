"""Test-Profil: eigene DB, SQLite für Geschwindigkeit (Docker/CI nutzt Postgres im CI-Plan)."""

from .base import *  # noqa: F401,F403

# Test-Instanz
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Test-DB: SQLite (lokal); im CI via env DATABASE_URL Postgres erzwingen.
if "DATABASE_URL" in env:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", default="flohmarkt_test"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST", default="localhost"),
            "PORT": env("DB_PORT", default="5432"),
            "CONN_MAX_AGE": 0,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db_test.sqlite3",
        }
    }

# Kein Spam bei Tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
