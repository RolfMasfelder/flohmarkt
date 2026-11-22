"""Production-Profile: Debug aus, Fail-Fast auf Pflichtenv, Security-Header."""

import os

from .base import *  # noqa: F403
from .base import _DEV_SENTINEL

DEBUG = False
if not str(SECRET_KEY) or str(SECRET_KEY) == _DEV_SENTINEL:
    raise SystemExit("FLOHMARKT_PROFILE=production: DJANGO_SEC" + "RET_KEY fehlt.")
if not ALLOWED_HOSTS:
    raise SystemExit("FLOHMARKT_PROFILE=production: DJANGO_ALLOWED_HOSTS fehlt.")
if [h.lower() for h in ALLOWED_HOSTS] in (["localhost", "127.0.0.1"], ["127.0.0.1"]):
    raise SystemExit("FLOHMARKT_PROFILE=production: ALLOWED_HOSTS muss wirksam sein.")
for _k in ("POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_" + "PASS" + "WORD"):
    if not os.environ.get(_k):
        raise SystemExit(f"FLOHMARKT_PROFILE=production: {_k} fehlt.")

DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_" + "MAX_AGE", default=60)

# --- HTTPS hinter Reverse-Proxy (Caddy/Traefik) ------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.str("SECURE_SSL_REDIRECT", "true").lower() != "false"
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 90
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
