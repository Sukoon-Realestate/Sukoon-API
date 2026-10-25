"""Purpose adapter for non-rent purchases using the shared payment records."""

from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from ..models import PaymentAttempt, PaymentQuote, SubscriptionPlan
from ..providers import checkout_available, get_rental_provider
from .billing_invoices import lock_purchase_invoice, require_actor
from .billing_settlement import settle_purchase
from .rental_phase2 import RentalConflict
from .rental_phase3 import quote_fingerprint


def validate_payable(invoice, user, revision, route=None):
    require_actor(user)
    from .purchase_routing import require_legacy_checkout

    if invoice.organization_id:
        from .commerce_access import organization_for

        organization_for(
            user, invoice.organization.id, pay=True, amount=invoice.amount_minor
        )
    store = (
        route
        and route.get("enabled")
        and route.get("route") in {"storekit", "play_billing", "hosted_checkout"}
    )
    if not store:
        require_legacy_checkout(invoice.purpose)
    if not store and not checkout_available():
        raise PermissionDenied(
            {
                "message": "Mock checkout is unavailable in this environment.",
                "code": "capability_unavailable",
            }
        )
    if invoice.purpose == "rent":
        raise RentalConflict("Use the rental invoice checkout for this obligation.")
    if invoice.purpose not in {
        "subscription",
        "advertising",
        "promotion",
        "maintenance",
    }:
        raise RentalConflict(
            "This obligation requires its canonical payment adapter.",
            code="purchase_route_unavailable",
        )
    if invoice.revision != revision:
        raise RentalConflict("Invoice revision conflict.", code="stale_revision")
    if invoice.status != "due":
        raise RentalConflict("This invoice is not payable.", code="invoice_not_payable")
    if (
        invoice.purpose == "subscription"
        and not SubscriptionPlan.objects.filter(
            id=invoice.purchase_snapshot["id"], active=True
        ).exists()
    ):
        raise RentalConflict(
            "The selected plan is unavailable.", code="plan_unavailable"
        )
    if invoice.purpose == "subscription" and route and route.get("sandbox_only"):
        from django.db.models import Q
        from ..models import AccountSubscription

        scopes = (
            ("tenant", "owner", "both")
            if invoice.purchase_snapshot["workspace"] == "both"
            else (invoice.workspace, "both")
        )
        if (
            AccountSubscription.objects.filter(
                **(
                    {"organization": invoice.organization}
                    if invoice.organization_id
                    else {"user": user, "organization__isnull": True}
                ),
                workspace__in=scopes,
                store_status__in=["", "active", "grace"],
            )
            .filter(
                Q(ends_at__gt=timezone.now())
                | Q(store_status="grace", grace_ends_at__gt=timezone.now())
            )
            .exists()
        ):
            raise RentalConflict(
                "A subscription is already active for this workspace.",
                code="subscription_active",
            )
    if invoice.payment_attempts.filter(
        payment_status__in=["created", "pending", "authorized"]
    ).exists():
        raise RentalConflict(
            "Resolve the original payment attempt.", code="payment_in_progress"
        )
    if invoice.purpose == "promotion":
        from .billing_sources import validate_promotion

        validate_promotion(invoice)
    if invoice.purpose == "maintenance":
        from .billing_sources import validate_maintenance_invoice

        validate_maintenance_invoice(invoice)
    if invoice.purpose == "advertising":
        from core_apps.advertising.models import Advertisement
        from .billing_advertising import validate_advertisement

        validate_advertisement(
            get_object_or_404(
                Advertisement, id=invoice.purchase_snapshot["subject_id"], owner=user
            )
        )


@transaction.atomic
def quote_purchase(user, invoice_id, body, *, platform="unknown"):
    invoice = lock_purchase_invoice(user, invoice_id)
    from .purchase_routing import routing_v1

    plan = (
        SubscriptionPlan.objects.filter(id=invoice.purchase_snapshot.get("id")).first()
        if invoice.purpose == "subscription"
        else None
    )
    route = routing_v1(
        invoice.purpose,
        platform,
        plan=plan,
        user=user,
        organization=bool(invoice.organization_id),
    )
    if (
        route["enabled"]
        and plan is not None
        and (
            invoice.amount_minor,
            invoice.currency,
            invoice.exponent,
        )
        != (plan.amount_minor, plan.currency, plan.exponent)
    ):
        raise RentalConflict(
            "The store price differs from this invoice.", code="store_price_mismatch"
        )
    validate_payable(invoice, user, body["expected_revision"], route)
    existing = PaymentQuote.objects.filter(
        invoice=invoice, request_key=body["request_key"]
    ).first()
    if existing:
        if existing.invoice_revision != body[
            "expected_revision"
        ] or existing.purchase_route != (route if route["enabled"] else {}):
            raise RentalConflict(
                "Quote request key conflict.", code="idempotency_conflict"
            )
        return existing
    expiry = timezone.now() + timedelta(minutes=5)
    return PaymentQuote.objects.create(
        invoice=invoice,
        request_key=body["request_key"],
        invoice_revision=invoice.revision,
        payer_amount_minor=invoice.amount_minor,
        currency=invoice.currency,
        exponent=invoice.exponent,
        purchase_route=route if route["enabled"] else {},
        policy_version="purchase-v1",
        fingerprint=quote_fingerprint(
            invoice, body["request_key"], invoice.amount_minor, expiry
        ),
        expires_at=expiry,
    )


def checkout_purchase(user, invoice_id, body):
    if PaymentQuote.objects.filter(
        id=body["quote_id"],
        invoice__id=invoice_id,
        purchase_route__route="hosted_checkout",
    ).exists():
        from .paymob_payments import checkout

        return checkout(user, invoice_id, body)
    return _checkout_purchase(user, invoice_id, body)


@transaction.atomic
def _checkout_purchase(user, invoice_id, body):
    # Same lock ordering for invoice creation/activation prevents duplicate
    # entitlements across two unpaid invoices or simultaneous workspace calls.
    get_user_model().objects.select_for_update().get(pk=user.pk)
    invoice = lock_purchase_invoice(user, invoice_id)
    existing = (
        PaymentAttempt.objects.filter(
            payer=user, invoice=invoice, request_key=body["request_key"]
        )
        .select_related("invoice", "quote")
        .first()
    )
    if existing:
        if (
            str(existing.quote.id) != str(body["quote_id"])
            or existing.invoice_revision != body["expected_revision"]
        ):
            raise RentalConflict(
                "This request key was used for different data.",
                code="idempotency_conflict",
            )
        return existing
    quote = get_object_or_404(
        PaymentQuote.objects.select_for_update(), id=body["quote_id"], invoice=invoice
    )
    route = quote.purchase_route
    if route.get("route") in {"storekit", "play_billing"}:
        from .purchase_routing import routing_v1

        platform = "ios" if route["route"] == "storekit" else "android"
        plan = SubscriptionPlan.objects.get(id=invoice.purchase_snapshot["id"])
        current_route = routing_v1(
            invoice.purpose,
            platform,
            plan=plan,
            user=user,
            organization=bool(invoice.organization_id),
        )
        if (
            not current_route["enabled"]
            or current_route["product_id"] != route["product_id"]
        ):
            raise RentalConflict(
                "Store purchases are unavailable.", code="purchase_route_unavailable"
            )
        if (invoice.amount_minor, invoice.currency, invoice.exponent) != (
            plan.amount_minor,
            plan.currency,
            plan.exponent,
        ):
            raise RentalConflict(
                "The store price changed.", code="store_price_mismatch"
            )
    validate_payable(invoice, user, body["expected_revision"], route)
    if quote.expires_at <= timezone.now():
        raise RentalConflict("The payment quote expired.", code="quote_expired")
    if (
        quote.invoice_revision != invoice.revision
        or quote.payer_amount_minor != invoice.amount_minor
    ):
        raise RentalConflict(
            "The invoice changed. Review it again.", code="stale_revision"
        )
    attempt = PaymentAttempt.objects.create(
        invoice=invoice,
        payer=user,
        quote=quote,
        request_key=body["request_key"],
        invoice_revision=invoice.revision,
        policy_version=quote.policy_version,
        quote_fingerprint=quote.fingerprint,
        amount_minor=quote.payer_amount_minor,
        currency=quote.currency,
        exponent=quote.exponent,
    )
    if route.get("enabled"):
        from .store_payments import create_intent

        attempt.payment_status = "pending"
        attempt.save(update_fields=["payment_status", "updated_at"])
        create_intent(user, attempt, route)
        return attempt
    # The adapter validates the isolated provider environment again. No real
    # gateway or card collection is invoked by this flow.
    reference = get_rental_provider().capture_purchase(attempt.id, body["request_key"])
    settle_purchase(invoice, attempt, reference)
    return attempt
