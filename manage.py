#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
    os.environ.setdefault("FLOHMARKT_PROFILE", "development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        msg = (
            "Impossible to import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        )
        raise SystemExit(msg) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
