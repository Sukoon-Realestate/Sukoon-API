from django.conf import settings
from ..providers import checkout_available, fake_provider_available


def invoice_payload(invoice, user, language="en", *, mobile=False, platform="unknown"):
    is_rent = invoice.purpose == "rent"
    # Rental settlement credits reduce the obligation without rewriting its
    # original amount or treating the credit as a cash payment.
    total_minor = invoice.amount_minor - (invoice.credits_minor if is_rent else 0)
    payable = invoice.status in {"due", "overdue", "partially_paid"}
    if is_rent:
        from .rental_phase3 import invoice_payment_allowed

        payable = invoice_payment_allowed(user, invoice)
    cancellable = False
    receipt = (
        invoice.payment_attempts.filter(payment_status="captured")
        .select_related("receipt")
        .first()
    )
    from .purchase_routing import routing, routing_v1

    plan = None
    if invoice.purpose == "subscription":
        from ..models import SubscriptionPlan

        plan = SubscriptionPlan.objects.filter(
            id=invoice.purchase_snapshot.get("id")
        ).first()
    route = routing_v1(
        invoice.purpose,
        platform,
        plan=plan,
        user=user,
        organization=bool(invoice.organization_id),
    )
    if plan and (invoice.amount_minor, invoice.currency, invoice.exponent) != (
        plan.amount_minor,
        plan.currency,
        plan.exponent,
    ):
        route.update(
            enabled=False,
            route="disabled",
            reason="store_price_mismatch",
            message="The invoice price no longer matches the store catalog.",
        )

    if not is_rent:
        authority = invoice.payer_id == user.pk and user.is_active
        if invoice.organization_id:
            from rest_framework.exceptions import PermissionDenied, ValidationError
            from .commerce_access import organization_for

            try:
                organization_for(
                    user, invoice.organization.id, pay=True, amount=invoice.amount_minor
                )
                authority = True
            except (PermissionDenied, ValidationError):
                authority = False
        unresolved = invoice.payment_attempts.filter(
            payment_status__in=["created", "pending", "authorized"]
        ).exists()
        payable = bool(
            authority
            and invoice.status == "due"
            and invoice.purpose
            in {"subscription", "advertising", "promotion", "maintenance"}
            and not unresolved
            and (
                route["enabled"]
                or (
                    checkout_available()
                    and fake_provider_available()
                    and not (
                        invoice.purpose == "subscription"
                        and getattr(
                            settings, "COMMERCE_SUBSCRIPTION_SANDBOX_ENABLED", False
                        )
                    )
                )
            )
        )
        cancellable = bool(
            authority
            and invoice.purpose in {"subscription", "advertising", "promotion"}
            and invoice.status == "due"
            and not unresolved
        )
    payload = {
        "purchase_routing": routing(invoice.purpose),
        "purchase_route": route,
        "organization_id": (
            str(invoice.organization.id) if invoice.organization_id else ""
        ),
        "fulfillment_status": fulfillment_status(invoice),
        "id": str(invoice.id),
        "reference": invoice.reference,
        "purpose": invoice.purpose,
        "workspace": invoice.workspace,
        "status": invoice.status,
        "revision": invoice.revision,
        "currency": invoice.currency,
        "exponent": invoice.exponent,
        "total_minor": total_minor,
        "paid_minor": invoice.applied_minor,
        "balance_minor": max(0, total_minor - invoice.applied_minor),
        "issued_at": invoice.created_at.isoformat(),
        "due_date": invoice.due_date.isoformat(),
        "paid_at": (
            receipt.confirmed_at.isoformat()
            if receipt and receipt.confirmed_at
            else None
        ),
        "receipt_id": (
            str(receipt.receipt.id) if receipt and hasattr(receipt, "receipt") else None
        ),
        "provider_mode": (
            "hosted"
            if receipt and hasattr(receipt, "paymob_payment")
            else (
                getattr(receipt, "store_intent", None).route_snapshot["route"]
                if receipt and hasattr(receipt, "store_intent")
                else (
                    "mock"
                    if receipt and receipt.provider_attempt_id.startswith("mock-")
                    else None
                )
            )
        ),
        "allowed_actions": (["pay"] if payable else [])
        + (["cancel"] if cancellable else []),
        "lines": [
            {
                "id": str(line.id),
                "description": (
                    line.source.get("description_ar", line.description)
                    if language == "ar"
                    else line.description
                ),
                "quantity": line.source.get("quantity", 1),
                "amount_minor": line.amount_minor,
                "currency": line.currency,
                "exponent": line.exponent,
            }
            for line in invoice.lines.all()
        ],
        "purchase": invoice.purchase_snapshot,
        "source": {
            "kind": "rent_invoice" if is_rent else invoice.purpose,
            "id": (
                str(invoice.id)
                if is_rent
                else invoice.purchase_snapshot.get(
                    "subject_id", invoice.purchase_snapshot.get("id")
                )
            ),
        },
    }

    if mobile:
        # These immutable source snapshots remain in storage and in the legacy
        # projection. Mobile renders the authoritative invoice/line amounts.
        payload.pop("purchase")
    return payload


def fulfillment_status(invoice):
    if invoice.purpose in {
        "rent",
        "maintenance",
        "deposit",
        "settlement",
        "adjustment",
    }:
        return "not_applicable"
    if invoice.purpose == "subscription":
        return "fulfilled" if hasattr(invoice, "subscription") else "pending"
    return "fulfilled" if invoice.status == "paid" and invoice.receipt_id else "pending"


def purchase_attempt_payload(attempt, *, include_checkout=True):
    receipt = getattr(attempt, "receipt", None)
    intent = getattr(attempt, "store_intent", None)
    paymob = getattr(attempt, "paymob_payment", None)
    payload = {
        "fulfillment_status": fulfillment_status(attempt.invoice),
        "retry_allowed": False,
        "id": str(attempt.id),
        "invoice_id": str(attempt.invoice.id),
        "request_key": str(attempt.request_key),
        "quote_id": str(attempt.quote.id),
        "revision": attempt.revision,
        "status": attempt.payment_status,
        "payment_status": attempt.payment_status,
        "provider_mode": (
            "hosted" if paymob else intent.route_snapshot["route"] if intent else "mock"
        ),
        "provider_reference": attempt.provider_attempt_id,
        "amount_minor": attempt.amount_minor,
        "currency": attempt.currency,
        "exponent": attempt.exponent,
        "receipt_id": str(receipt.id) if receipt else None,
        "confirmed_at": (
            attempt.confirmed_at.isoformat() if attempt.confirmed_at else None
        ),
    }

    if paymob:
        from .paymob_payments import session_payload

        if include_checkout:
            payload["checkout_session"] = session_payload(attempt)
        payload["provider_environment"] = paymob.environment
        payload["failure_code"] = paymob.failure_code
    if intent:
        payload["store_session"] = {
            "session_id": str(intent.id),
            "invoice_id": str(attempt.invoice.id),
            "payment_attempt_id": str(attempt.id),
            "app_account_token": str(intent.account.app_account_token),
            "expires_at": intent.expires_at.isoformat(),
            "purchase_route": intent.route_snapshot,
        }
    return payload


def purchase_quote_payload(quote):
    return {
        "id": str(quote.id),
        "invoice_id": str(quote.invoice.id),
        "invoice_revision": quote.invoice_revision,
        "amount_minor": quote.payer_amount_minor,
        "currency": quote.currency,
        "exponent": quote.exponent,
        "expires_at": quote.expires_at.isoformat(),
        "provider_mode": (
            "hosted"
            if quote.purchase_route.get("route") == "hosted_checkout"
            else quote.purchase_route.get("route", "mock")
        ),
        "purchase_route": quote.purchase_route,
        **(
            {"provider_environment": "sandbox"}
            if quote.purchase_route.get("sandbox_only") is True
            else {}
        ),
    }
