"""API-only rental provider simulation; select explicitly on isolated staging."""

from os import getenv

from django.core.exceptions import ImproperlyConfigured

from .staging import *  # noqa: F401,F403

RENTAL_PROVIDER_WEBHOOK_SECRET = getenv("RENTAL_PROVIDER_WEBHOOK_SECRET", "")
RENTAL_PROVIDER_BACKEND = "fake"
RENTAL_FAKE_PROVIDER_ALLOWED = True
RENTAL_CHECKOUT_ENABLED = True
RENTAL_CHECKOUT_ALLOWED_ORIGINS = ["https://fake-rental-provider.test"]
RENTAL_CHECKOUT_RETURN_URL = "https://fake-rental-provider.test/payments/return"
PLANNING_ENABLED_SERVICES = [
    "lifestyle",
    "roommates",
    "housing_groups",
    "group_visits",
    "group_applications",
    "housing_requests",
    "housing_offers",
    "condition_reports",
    "move_out_notices",
    "replacements",
    "commute",
    "tenant_assistant",
]
PLANNING_MOCK_DISCOVERY = True

if not RENTAL_PROVIDER_WEBHOOK_SECRET:  # noqa: F405
    raise ImproperlyConfigured(
        "Staging mock mode requires RENTAL_PROVIDER_WEBHOOK_SECRET."
    )
