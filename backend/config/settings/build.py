"""Static collection only. No database, broker, provider or runtime secrets."""

from .base import *  # noqa: F401,F403

SECRET_KEY = "static-build-only-not-a-runtime-signing-key"
DEBUG = False
ADMIN_URL = "admin/"
DATABASES = {"default": {"ENGINE": "django.db.backends.dummy"}}
