"""API-only rental provider simulation; select explicitly on isolated staging."""

from os import getenv

from django.core.exceptions import ImproperlyConfigured

from config.planning import SERVICES
from config.rental_simulation import enabled_from_env
from .staging import *  # noqa: F401,F403

RENTAL_PROVIDER_WEBHOOK_SECRET = getenv("RENTAL_PROVIDER_WEBHOOK_SECRET", "")
RENTAL_PROVIDER_BACKEND = "fake"
RENTAL_FAKE_PROVIDER_ALLOWED = enabled_from_env()
RENTAL_CHECKOUT_ENABLED = RENTAL_FAKE_PROVIDER_ALLOWED
RENTAL_CHECKOUT_ALLOWED_ORIGINS = ["https://fake-rental-provider.test"]
RENTAL_CHECKOUT_RETURN_URL = "https://fake-rental-provider.test/payments/return"
PLANNING_ENABLED_SERVICES = list(SERVICES)
PLANNING_MOCK_DISCOVERY = RENTAL_FAKE_PROVIDER_ALLOWED

if RENTAL_FAKE_PROVIDER_ALLOWED and not RENTAL_PROVIDER_WEBHOOK_SECRET:  # noqa: F405
    raise ImproperlyConfigured(
        "Staging mock mode requires RENTAL_PROVIDER_WEBHOOK_SECRET."
    )
