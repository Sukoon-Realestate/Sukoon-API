"""Durable invoice checkout, server inquiry and canonical financial allocation."""

import re
import secrets
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from ..models import (
    CheckoutSession,
    IdempotencyRecord,
    PaymobPayment,
    PaymentAttempt,
    PaymentQuote,
    RentInvoice,
)
from . import paymob_client as client
from .billing_invoices import authorized_invoice, lock_purchase_invoice
from .rental_phase2 import RentalConflict, fingerprint, remember_mutation


def lock_invoice(user, identity):
    get_user_model().objects.select_for_update().get(pk=user.pk)
    invoice = authorized_invoice(user, identity)
    if invoice.lease_id:
        from .rental_lifecycle.locks import lock_financial_lease

        lock_financial_lease(invoice.lease)
        return authorized_invoice(user, identity, lock=True)
    return lock_purchase_invoice(user, identity)


def navigation(attempt):
    origins = [
        *client.CHECKOUT_ORIGINS,
        *getattr(settings, "PAYMOB_CHECKOUT_EXTRA_ORIGINS", []),
    ]
    from urllib.parse import urlparse

    for origin in origins:
        parts = urlparse(origin)
        if (
            parts.scheme != "https"
            or not parts.hostname
            or "*" in parts.netloc
            or parts.username
            or parts.path not in {"", "/"}
            or parts.query
            or parts.fragment
        ):
            raise client.PaymobUnavailable()
    return {
        "allowed_origins": list(dict.fromkeys(origins)),
        "return_url": settings.PAYMOB_RETURN_URL,
        "return_state": secrets.token_urlsafe(32),
        "payment_attempt_id": str(attempt.id),
        "external_schemes": [],
    }


@transaction.atomic
def prepare(user, invoice_id, body, *, rental):
    invoice = lock_invoice(user, invoice_id)
    if rental and invoice.purpose == "subscription":
        raise RentalConflict(
            "Use the subscription invoice checkout for this purchase.",
            code="purchase_route_unavailable",
        )
    existing = (
        PaymentAttempt.objects.filter(
            invoice=invoice, payer=user, request_key=body["request_key"]
        )
        .select_related("quote")
        .first()
    )
    operation = f"invoice.checkout.{invoice.id}"
    record = IdempotencyRecord.objects.filter(
        user=user, operation=operation, request_key=str(body["request_key"])
    ).first()
    if record:
        if record.recovery_status == "absent_final":
            raise RentalConflict(
                "This operation was closed without execution.",
                code="operation_closed_without_execution",
            )
        if record.fingerprint != fingerprint(body):
            raise RentalConflict(
                "This request key has different inputs.", code="idempotency_conflict"
            )
    if existing:
        if (
            str(existing.quote.id) != str(body["quote_id"])
            or existing.invoice_revision != body["expected_revision"]
        ):
            raise RentalConflict(
                "This request key has different inputs.", code="idempotency_conflict"
            )
        return existing.paymob_payment, False
    if invoice.purpose != "subscription" and not client.checkout_ready():
        raise RentalConflict(
            "Paymob checkout is unavailable.", code="purchase_route_unavailable"
        )
    if rental:
        from .company.tenancy_access import can_pay
        from .rental_phase3 import invoice_payment_allowed

        if not can_pay(invoice.lease, user):
            raise PermissionDenied("Current payer authority is required.")
        if not invoice_payment_allowed(user, invoice):
            raise RentalConflict(
                "The invoice is not payable.", code="payment_in_progress"
            )
    else:
        from .billing_payments import validate_payable

        route = {"route": "hosted_checkout", "enabled": True}
        if invoice.purpose == "subscription":
            from ..models import SubscriptionPlan
            from .purchase_routing import routing_v1

            plan = SubscriptionPlan.objects.filter(
                id=invoice.purchase_snapshot.get("id")
            ).first()
            route = routing_v1(
                "subscription",
                "android",
                plan=plan,
                user=user,
                organization=bool(invoice.organization_id),
            )
            if not route.get("sandbox_only") or not route["enabled"]:
                raise RentalConflict(
                    "Subscription sandbox checkout is unavailable.",
                    code="purchase_route_unavailable",
                )
            if (invoice.amount_minor, invoice.currency, invoice.exponent) != (
                plan.amount_minor,
                plan.currency,
                plan.exponent,
            ):
                raise RentalConflict("The plan price changed.", code="invoice_changed")
        validate_payable(
            invoice,
            user,
            body["expected_revision"],
            route,
        )
    if invoice.purpose not in {"rent", "maintenance", "subscription"}:
        raise RentalConflict(
            "This product cannot use Paymob checkout.",
            code="purchase_route_unavailable",
        )
    if invoice.revision != body["expected_revision"]:
        raise RentalConflict("The invoice changed.", code="invoice_changed")
    quote = get_object_or_404(
        PaymentQuote.objects.select_for_update(), id=body["quote_id"], invoice=invoice
    )
    if invoice.purpose == "subscription" and (rental or quote.purchase_route != route):
        raise RentalConflict(
            "The subscription sandbox route changed. Review the invoice again.",
            code="purchase_route_unavailable",
        )
    if quote.expires_at <= timezone.now():
        raise RentalConflict("The quote expired.", code="quote_expired")
    if rental:
        from .chargebacks.funding import quote_amount

        balance = quote_amount(invoice)
    else:
        balance = invoice.amount_minor - invoice.applied_minor
    if (
        quote.invoice_revision != invoice.revision
        or quote.payer_amount_minor != balance
        or quote.currency != invoice.currency
        or quote.exponent != invoice.exponent
    ):
        raise RentalConflict(
            "The quote no longer matches the invoice.", code="invoice_changed"
        )
    # Validate billing before recording a new external operation. Nothing is stored.
    client.billing_for_invoice(user, invoice, quote)
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
        payment_status="pending",
    )
    payment = PaymobPayment.objects.create(
        attempt=attempt,
        reference=f"sukoon:payment:{attempt.id}",
        integration_id=settings.PAYMOB_INTEGRATION_ID,
    )
    nav = navigation(attempt)
    session = CheckoutSession.objects.create(
        invoice=invoice,
        payer=user,
        attempt=attempt,
        quote=quote,
        request_key=body["request_key"],
        hosted_url="",
        expires_at=timezone.now() + timedelta(minutes=15),
        status="pending",
        navigation=nav,
        return_state=nav["return_state"],
    )
    remember_mutation(
        user=user,
        operation=operation,
        request_key=body["request_key"],
        payload=body,
        request_subject_id=invoice.id,
        result_subject_id=session.id,
        result_revision=attempt.revision,
        resource=session_payload(attempt),
        response_status=201,
    )
    return payment, True


def checkout(user, invoice_id, body, *, rental=False):
    # Network work must never occur inside a transaction that could erase its intent.
    if connection.in_atomic_block and not getattr(
        settings, "PAYMOB_ALLOW_TRANSACTIONAL_TESTS", False
    ):
        raise client.PaymobUnavailable()
    payment, created = prepare(user, invoice_id, body, rental=rental)
    if created:
        session = payment.attempt.checkout_session
        redirect = (
            session.navigation["return_url"]
            + "?"
            + urlencode(
                {
                    "state": session.return_state,
                    "payment_attempt_id": str(payment.attempt.id),
                }
            )
        )
        try:
            response = client.create_intention(
                payment,
                client.billing_for_invoice(
                    user, payment.attempt.invoice, payment.attempt.quote
                ),
                redirect,
            )
            bind_intention(payment, response)
        except Exception:
            PaymobPayment.objects.filter(pk=payment.pk).exclude(
                status="captured"
            ).update(status="outcome_unknown", failure_code="outcome_unknown")
            raise client.PaymobUnavailable() from None
    return PaymentAttempt.objects.select_related(
        "invoice", "quote", "checkout_session", "paymob_payment"
    ).get(pk=payment.attempt_id)


@transaction.atomic
def bind_intention(payment, response):
    payment = (
        PaymobPayment.objects.select_for_update()
        .select_related("attempt")
        .get(pk=payment.pk)
    )
    order_id = str(response.get("intention_order_id", ""))
    intention = response.get("id")
    if (
        not re.fullmatch(r"[0-9]{1,18}", order_id)
        or not isinstance(intention, str)
        or not intention.startswith("pi_test_")
        or response.get("special_reference") != payment.reference
    ):
        raise client.PaymobUnavailable()
    detail = response.get("intention_detail", {})
    if (
        detail.get("amount") != payment.attempt.amount_minor
        or detail.get("currency") != payment.attempt.currency
    ):
        raise client.PaymobUnavailable()
    url = client.checkout_url(response.get("client_secret"))
    payment.intention_id, payment.order_id, payment.status, payment.failure_code = (
        intention,
        order_id,
        "ready",
        "",
    )
    payment.save()
    session = CheckoutSession.objects.select_for_update().get(attempt=payment.attempt)
    session.hosted_url, session.provider_session_id, session.status = (
        url,
        intention,
        "created",
    )
    session.save()
    record = IdempotencyRecord.objects.select_for_update().get(
        user=payment.attempt.payer,
        operation=f"invoice.checkout.{payment.attempt.invoice.id}",
        request_key=str(payment.attempt.request_key),
    )
    record.response_data["resource"] = session_payload(payment.attempt)
    record.save(update_fields=["response_data", "updated_at"])


def session_payload(attempt):
    session = attempt.checkout_session
    # Old pending sessions must follow the provider's canonical redirect too.
    # Project only pinned provider origins; preserve their original return state,
    # URL, expiry and identity without creating another intention or rewriting DB.
    nav = {
        **session.navigation,
        "allowed_origins": list(
            dict.fromkeys(
                [
                    *session.navigation.get("allowed_origins", []),
                    *client.CHECKOUT_ORIGINS,
                ]
            )
        ),
    }
    return {
        "session_id": str(session.id),
        "payment_attempt_id": str(attempt.id),
        "invoice_id": str(attempt.invoice.id),
        "quote_id": str(attempt.quote.id),
        "request_key": str(attempt.request_key),
        "invoice_revision": attempt.invoice_revision,
        "status": attempt.payment_status,
        "amount": {
            "amount_minor": attempt.amount_minor,
            "currency": attempt.currency,
            "exponent": attempt.exponent,
        },
        "checkout_url": session.hosted_url,
        "expires_at": session.expires_at.isoformat(),
        "provider_mode": "hosted",
        "provider_environment": "sandbox",
        "navigation": nav,
    }


def rental_response(attempt):
    record = IdempotencyRecord.objects.get(
        user=attempt.payer,
        operation=f"invoice.checkout.{attempt.invoice.id}",
        request_key=str(attempt.request_key),
    )
    return {**record.response_data, "resource": session_payload(attempt)}


def reconcile(payment, *, transaction_id=None):
    # This remains available when the NEW-sale switch is disabled.
    snapshot = client.inquiry(payment, transaction_id)
    try:
        return apply_snapshot(payment, snapshot)
    except RentalConflict as exc:
        PaymobPayment.objects.filter(pk=payment.pk).update(
            status="review", failure_code=str(exc.get_codes())[:80]
        )
        from .rental_lifecycle.cases import open_system_case
        from ..models import OwnerPayable

        OwnerPayable.objects.filter(payment_attempt=payment.attempt).exclude(
            payout_status__in=["succeeded", "submitted", "processing"]
        ).update(
            payout_status="held",
            blocking_reasons=["Paymob reconciliation is required."],
        )
        attempt = payment.attempt
        open_system_case(
            kind="payment_unknown",
            source_key=f"paymob-review:{payment.id}",
            lease=attempt.invoice.lease,
            attempt=attempt,
            reason="Paymob payment needs financial reconciliation.",
            next_action="Review the original provider transaction before any new charge or refund.",
        )
        raise


@transaction.atomic
def apply_snapshot(payment, snapshot):
    # Provider facts are recorded even if the payer's later authority changed.
    candidate = PaymobPayment.objects.select_related(
        "attempt__invoice__lease", "attempt__payer"
    ).get(pk=payment.pk)
    invoice = candidate.attempt.invoice
    get_user_model().objects.select_for_update().get(pk=candidate.attempt.payer_id)
    if invoice.lease_id:
        from .rental_lifecycle.locks import lock_financial_lease

        lock_financial_lease(invoice.lease)
    elif invoice.organization_id:
        from ..models import Company

        Company.objects.select_for_update().get(pk=invoice.organization_id)
    invoice = RentInvoice.objects.select_for_update().get(pk=invoice.pk)
    payment = PaymobPayment.objects.select_for_update().get(pk=payment.pk)
    attempt = PaymentAttempt.objects.select_for_update().get(pk=payment.attempt_id)
    order = snapshot.get("order") or {}
    tx_id, order_id = str(snapshot.get("id", "")), str(order.get("id", ""))
    if (
        not re.fullmatch(r"[0-9]{1,18}", tx_id)
        or not re.fullmatch(r"[0-9]{1,18}", order_id)
        or str(snapshot.get("integration_id")) != payment.integration_id
        or snapshot.get("is_live") is not False
        or snapshot.get("currency") != attempt.currency
        or type(snapshot.get("amount_cents")) is not int
        or snapshot["amount_cents"] != attempt.amount_minor
        or order.get("merchant_order_id") != payment.reference
        or (payment.order_id and payment.order_id != order_id)
    ):
        raise RentalConflict(
            "Paymob payment identity or amount mismatch.",
            code="provider_payment_mismatch",
        )
    if any(
        type(snapshot.get(key)) is not bool
        for key in (
            "success",
            "pending",
            "is_auth",
            "is_capture",
            "is_refunded",
            "is_voided",
            "error_occured",
            "has_parent_transaction",
        )
    ):
        raise RentalConflict(
            "The provider state is incomplete.", code="outcome_unknown"
        )
    payment.order_id = order_id
    if (
        snapshot["is_refunded"]
        and not snapshot["is_voided"]
        and not snapshot["has_parent_transaction"]
        and payment.transaction_id == tx_id
    ):
        from django.db.models import Sum

        accounted = (
            payment.refunds.filter(
                status="confirmed", refund__status="succeeded"
            ).aggregate(total=Sum("amount_minor"))["total"]
            or 0
        )
        if (
            accounted > 0
            and type(snapshot.get("refunded_amount_cents")) is int
            and snapshot["refunded_amount_cents"] == accounted
        ):
            payment.status, payment.failure_code = "captured", ""
            payment.reconciled_at = timezone.now()
            payment.save()
            if invoice.purpose == "rent" and snapshot.get("is_settled") is True:
                confirm_settlement(attempt, tx_id)
            return attempt
    if (
        snapshot["is_refunded"]
        or snapshot["is_voided"]
        or snapshot["has_parent_transaction"]
    ):
        raise RentalConflict(
            "This payment requires reversal reconciliation.",
            code="provider_reversal_review",
        )
    if snapshot["pending"] or not snapshot["success"] or snapshot["error_occured"]:
        # A declined transaction does not prove the checkout/order is closed.
        payment.failure_code = (
            "provider_pending" if snapshot["pending"] else "provider_declined"
        )
    elif snapshot["is_auth"] and not snapshot["is_capture"]:
        if attempt.payment_status not in {"captured", "chargedback"}:
            attempt.payment_status = "authorized"
            attempt.revision += 1
            attempt.save()
        payment.failure_code = ""
    else:
        if payment.transaction_id and payment.transaction_id != tx_id:
            raise RentalConflict(
                "A second capture needs reconciliation.", code="duplicate_capture"
            )
        payment.transaction_id = tx_id
        if attempt.payment_status not in {"captured", "chargedback"}:
            attempt.provider_attempt_id = tx_id
            attempt.save(update_fields=["provider_attempt_id", "updated_at"])
            if invoice.purpose == "rent":
                from .rental_phase3_parts.capture_attempt import _capture_attempt

                _capture_attempt(attempt)
            elif invoice.purpose == "maintenance" or (
                invoice.purpose == "subscription"
                and not invoice.organization_id
                and payment.environment == "sandbox"
                and attempt.quote.purchase_route.get("sandbox_only") is True
                and attempt.quote.purchase_route.get("provider_environment")
                == "sandbox"
                and attempt.quote.purchase_route.get("route") == "hosted_checkout"
            ):
                from .billing_settlement import settle_purchase

                if (
                    invoice.status != "due"
                    or invoice.applied_minor
                    or invoice.revision != attempt.invoice_revision
                ):
                    raise RentalConflict(
                        "The original service invoice changed.", code="invoice_changed"
                    )
                settle_purchase(invoice, attempt, tx_id, provider_mode="hosted")
            else:
                raise RentalConflict(
                    "Paymob cannot fulfill this product.", code="invalid_payment_domain"
                )
        payment.status, payment.failure_code = "captured", ""
        if invoice.purpose == "rent" and snapshot.get("is_settled") is True:
            confirm_settlement(attempt, tx_id)
        CheckoutSession.objects.filter(attempt=attempt).update(status="completed")
    payment.reconciled_at = timezone.now()
    payment.save()
    return attempt


def process_callback(event):
    payment = (
        PaymobPayment.objects.filter(order_id=event.order_id)
        .select_related("attempt__invoice")
        .first()
    )
    if payment:
        reconcile(payment, transaction_id=event.transaction_id)


def confirm_settlement(attempt, tx_id):
    import hashlib
    import json
    from ..models import ProviderWebhookEvent
    from .rental_phase3 import process_provider_event

    facts = {"amount_minor": attempt.amount_minor, "currency": attempt.currency}
    event, _ = ProviderWebhookEvent.objects.get_or_create(
        provider="paymob",
        provider_event_id=f"settled:{tx_id}",
        defaults={
            "event_type": "payment.settled",
            "payment_attempt": attempt,
            "signature_valid": True,
            "payload_digest": hashlib.sha256(
                json.dumps(facts, sort_keys=True).encode()
            ).hexdigest(),
            "payload": facts,
        },
    )
    process_provider_event(event)
    attempt.refresh_from_db()
