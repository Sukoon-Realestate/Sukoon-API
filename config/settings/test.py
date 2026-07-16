from os import getenv

from .base import *  # noqa
from .base import SIMPLE_JWT

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = False

ADMIN_URL = "admin/"

SITE_NAME = "Darak"

DOMAIN = "localhost"

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Use faster hasher in tests — never use in production
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

COOKIE_SECURE = False

SIMPLE_JWT = {
    **SIMPLE_JWT,
    "SIGNING_KEY": "test-jwt-signing-key-not-for-production",
}

# ? In-memory layer keeps consumer tests hermetic (no Redis dependency in CI)
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
