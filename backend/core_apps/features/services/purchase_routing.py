"""Native-store routing with an explicit, account-scoped subscription sandbox."""

from django.conf import settings
from ..providers import fake_provider_available
from .rental_phase2 import RentalConflict

DIGITAL_PURPOSES = {"subscription", "advertising", "promotion"}
PHYSICAL_PURPOSES = {"rent", "deposit", "maintenance", "settlement", "adjustment"}


def subscription_sandbox_ready(user, plan):
    from .paymob_client import sandbox_ready

    return bool(
        getattr(settings, "COMMERCE_SUBSCRIPTION_SANDBOX_ENABLED", False)
        and user is not None
        and user.is_authenticated
        and user.is_active
        and str(user.id)
        in getattr(settings, "COMMERCE_SUBSCRIPTION_SANDBOX_USER_IDS", [])
        and plan is not None
        and plan.active
        and plan.audience == "personal"
        and plan.period_months in {1, 12}
        and sandbox_ready()
    )


def routing(
    purpose,
    platform="unknown",
    *,
    product_id="",
    plan=None,
    user=None,
    organization=False,
):
    category = (
        "digital_purchase"
        if purpose in DIGITAL_PURPOSES
        else (
            "rental_obligation"
            if purpose in {"rent", "deposit"}
            else (
                "service_payment"
                if purpose in {"maintenance", "settlement", "adjustment"}
                else "unknown"
            )
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
    if (
        purpose == "subscription"
        and not organization
        and subscription_sandbox_ready(user, plan)
    ):
        return {
            "category": category,
            "route": "hosted_checkout",
            "enabled": True,
            "provider": "paymob",
            "provider_mode": "hosted",
            "provider_environment": "sandbox",
            "sandbox_only": True,
            "external_checkout_allowed": True,
            "product_id": "",
            "reason": "",
        }
    if purpose == "subscription" and plan is not None and route:
        from .store_payments import product_route

        return product_route(plan, platform)
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
    from .paymob_client import checkout_ready

    enabled = purpose in {"rent", "maintenance"} and checkout_ready()
    return {
        "category": category,
        "route": "egyptian_psp",
        "enabled": enabled,
        "provider_mode": "hosted",
        "provider_environment": "sandbox",
        "provider": "paymob",
        "reason": "" if enabled else "live_provider_not_configured",
        "external_checkout_allowed": True,
    }


def require_legacy_checkout(purpose):
    # Explicit isolated simulation remains labelled mock. Platform claims never
    # turn an unreviewed digital purchase into an approved web exception.
    if purpose == "subscription" and getattr(
        settings, "COMMERCE_SUBSCRIPTION_SANDBOX_ENABLED", False
    ):
        raise RentalConflict(
            "An enabled subscription sandbox route is required.",
            code="purchase_route_unavailable",
        )
    if fake_provider_available():
        return
    if purpose in DIGITAL_PURPOSES or purpose not in PHYSICAL_PURPOSES:
        raise RentalConflict(
            "This product requires an approved purchase route and server receipt verification.",
            code="purchase_route_unavailable",
        )


def routing_v1(
    purpose, platform="unknown", *, plan=None, user=None, organization=False
):
    value = routing(purpose, platform, plan=plan, user=user, organization=organization)
    return {
        **value,
        "contract_version": 1,
        "route": (
            "hosted_checkout" if value["route"] == "egyptian_psp" else value["route"]
        ),
        "product_type": (
            "subscription"
            if purpose == "subscription"
            else "consumable" if purpose in DIGITAL_PURPOSES else ""
        ),
        "message": (
            value.get("message", "")
            if value["enabled"]
            else "Purchases are unavailable until the payment route is configured."
        ),
    }
