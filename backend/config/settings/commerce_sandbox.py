"""Isolated local catalog preview; never points at the application's real database."""

from .local_sqlite import *  # noqa: F401,F403
from .local_sqlite import BASE_DIR

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "commerce_sandbox.sqlite3",
    }
}
COMMERCE_STORE_PURCHASES_ENABLED = False
COMMERCE_STORE_ADAPTERS = {}
COMMERCE_ENTITLEMENTS_ENABLED = False
