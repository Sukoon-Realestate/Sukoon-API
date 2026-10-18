"""Conservative store routing. An unreviewed digital SKU cannot use a rental PSP."""

from django.conf import settings
from ..providers import fake_provider_available
from .rental_phase2 import RentalConflict

DIGITAL_PURPOSES = {"subscription", "advertising"}
PHYSICAL_PURPOSES = {"rent", "deposit", "maintenance"}


def routing(purpose, platform="unknown", *, product_id=""):
    category = (
        "digital_purchase"
        if purpose in DIGITAL_PURPOSES
        else (
            "rental_obligation"
            if purpose in {"rent", "deposit"}
            else "service_payment" if purpose == "maintenance" else "unknown"
        )
    )
    route = (
        "storekit"
        if platform == "ios"
        else "play_billing" if platform == "android" else None
    )
    if category == "unknown" or platform not in {"ios", "android", "web"}:
        return {
            "category": category,
            "route": "disabled",
            "enabled": False,
            "reason": "unknown_product_or_platform",
            "product_id": product_id,
        }
    if purpose in DIGITAL_PURPOSES:
        return {
            "category": category,
            "route": "disabled",
            "required_route": route,
            "enabled": False,
            "reason": "store_product_and_receipt_verification_not_configured",
            "product_id": product_id,
            "external_checkout_allowed": False,
            "policy_reviewed_on": "2026-10-18",
        }
    return {
        "category": category,
        "route": "egyptian_psp",
        "enabled": False,
        "reason": "live_provider_not_configured",
        "external_checkout_allowed": True,
    }


def require_legacy_checkout(purpose):
    # Explicit isolated simulation remains labelled mock. Platform claims never
    # turn an unreviewed digital purchase into an approved web exception.
    if fake_provider_available():
        return
    if purpose in DIGITAL_PURPOSES or purpose not in PHYSICAL_PURPOSES:
        raise RentalConflict(
            "This product requires an approved purchase route and server receipt verification.",
            code="purchase_route_unavailable",
        )
