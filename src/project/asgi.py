import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
os.environ.setdefault("FLOHMARKT_PROFILE", "production")

application = get_asgi_application()
