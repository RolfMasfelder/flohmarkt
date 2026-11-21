"""Flohmarkt-Test-Suite (separates tests/-Verzeichnis, wie gewünscht).

Auswahl:
  - tests.unit.*     — Domain-Logik (keine DB)
  - tests.models.*   — Django-Model-Tests (DB via pytest-django)
  - tests.api.*      — DRF-Endpoints (DB via pytest-django)
  - tests.integration/ — Adapter-Mock-Level (noch zu befüllen)
"""
