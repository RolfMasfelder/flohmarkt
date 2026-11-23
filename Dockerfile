# syntax=docker/dockerfile:1
# flohmarkt — Django 6.1 / Python 3.14, Gunicorn + WhiteNoise
# src-Layout: /app/src + PYTHONPATH (kein Package-Install nötig).
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src \
    DJANGO_SETTINGS_MODULE=project.settings \
    FLOHMARKT_PROFILE=production

WORKDIR /app

# System-Abhängigkeiten: libpq5 (psycopg), ca-certificates, libjpeg (Pillow-Fallback)
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates libpq5 libjpeg62-turbo \
 && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten (eigene Versionen, siehe pyproject.toml)
RUN python -m pip install \
    "Django>=6.1,<6.2" \
    "djangorestframework>=3.18,<4.0" \
    "drf-spectacular>=0.30,<0.31" \
    "psycopg[binary]>=3.3,<4.0" \
    "httpx>=0.28,<0.29" \
    "django-environ>=0.14,<0.15" \
    "whitenoise>=6.12,<7.0" \
    "gunicorn>=27.0,<28.0"

# Quellcode
COPY manage.py ./
COPY src ./src

# Statics vor-abbilden (WhiteNoise liefert sie daraus)
# Buildzeit ohne Produktivguards: Test-Profil, Dummy-Env (nichts persistiert)
RUN FLOHMARKT_PROFILE=testing DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput

# Nicht-root-Betrieb
RUN useradd --create-home --uid 1000 app \
 && mkdir -p /data/media /data/symbols \
 && chown -R app:app /data
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/healthz/', timeout=3).status==200 else 1)"

CMD ["gunicorn", "project.wsgi:application", "-b", "0.0.0.0:8000", "-w", "2", "--access-logfile", "-"]
