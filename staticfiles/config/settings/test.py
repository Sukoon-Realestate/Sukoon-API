from os import getenv

from .base import *  # noqa
from .base import SIMPLE_JWT

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = False

ADMIN_URL = "admin/"

SITE_NAME = "Test"

DOMAIN = "localhost"

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": getenv("POSTGRES_DB", "test_db"),
        "USER": getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": getenv("POSTGRES_PASSWORD", "postgres"),
        "HOST": getenv("POSTGRES_HOST", "localhost"),
        "PORT": getenv("POSTGRES_PORT", "5432"),
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
