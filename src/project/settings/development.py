"""Development-Profile: Debug an, lauter Logging."""

from .base import *  # noqa: F403

DEBUG = True
INTERNAL_IPS = ["127.0.0.1"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
