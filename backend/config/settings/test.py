from os import getenv

from .base import *  # noqa
from .base import SIMPLE_JWT

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = False

ADMIN_URL = "admin/"

SITE_NAME = "Sukoon"

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

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
RENTAL_PROVIDER_BACKEND = "fake"
RENTAL_RUNTIME_ENVIRONMENT = "test"
RENTAL_FAKE_PROVIDER_ALLOWED = True
RENTAL_PROVIDER_WEBHOOK_SECRET = "test-rental-provider-secret"
RENTAL_CHECKOUT_ENABLED = True
RENTAL_CHECKOUT_ALLOWED_ORIGINS = ["https://fake-rental-provider.test"]
RENTAL_CHECKOUT_RETURN_URL = "https://fake-rental-provider.test/payments/return"
RENTAL_CHECKOUT_EXTERNAL_SCHEMES = []

# Dummy Cloudinary config for tests to allow URL generation locally
import cloudinary

cloudinary.config(
    cloud_name="test_cloud",
    api_key="test_key",
    api_secret="test_secret",
)
