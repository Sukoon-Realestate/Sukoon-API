"""Opt-in PostgreSQL tests; never inherit production database credentials."""

from os import environ

from .test import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": environ["TEST_POSTGRES_DB"],
        "USER": environ["TEST_POSTGRES_USER"],
        "PASSWORD": environ.get("TEST_POSTGRES_PASSWORD", ""),
        "HOST": environ.get("TEST_POSTGRES_HOST", "127.0.0.1"),
        "PORT": environ.get("TEST_POSTGRES_PORT", "5432"),
    }
}
