"""ASGI config for complaint_tracking_system project."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "complaint_tracking_system.settings")

application = get_asgi_application()
