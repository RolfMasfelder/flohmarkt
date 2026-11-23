"""Settings-Selektor.

``DJANGO_SETTINGS_MODULE`` muss auf ``project.settings`` (oder
``project.settings.testing``) zeigen. Das konkrete Profil wird über
die Umgebungsvariable ``FLOHMARKT_PROFILE`` gewählt:

- ``development`` (Default)
- ``production``
- ``testing``
"""

import importlib
import os

_PROFILE = os.environ.get("FLOHMARKT_PROFILE", "development")
if _PROFILE not in {"development", "production", "testing"}:
    raise SystemExit(
        f"Unbekanntes FLOHMARKT_PROFILE: {_PROFILE!r} — erlaubt: development | production | testing"
    )

# Basis zuerst, dann Profil überschreibt
from project.settings import base  # noqa: E402

_globals = globals()
for _name, _value in [(k, v) for k, v in vars(base).items() if not k.startswith("_")]:
    _globals[_name] = _value

_profile_module = importlib.import_module(f"project.settings.{_PROFILE}")
for _name, _value in [(k, v) for k, v in vars(_profile_module).items() if not k.startswith("_")]:
    _globals[_name] = _value
