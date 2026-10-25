"""Resume one original hosted payment. Never create a replacement intention."""

import uuid
from urllib.parse import urlencode
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..models import CheckoutSession, IdempotencyRecord, PaymentAttempt, PaymobPayment
from . import paymob_client as client
from .paymob_payments import apply_snapshot
from .payment_session_proof import verified_expiry
from .rental_phase2 import RentalConflict


def resume(user, attempt, request_key):
    try:
        key = str(uuid.UUID(str(request_key)))
    except (ValueError, TypeError):
        raise ValidationError({"request_key": "A UUID is required."})
    if attempt.payer_id != user.pk:
        raise PermissionDenied("Only the original payer can resume payment.")
    if attempt.invoice.organization_id:
        from .commerce_access import organization_for

        organization_for(
            user, attempt.invoice.organization.id, pay=True, amount=attempt.amount_minor
        )
    if attempt.invoice.purpose == "rent":
        from .company.tenancy_access import can_pay

        if not can_pay(attempt.invoice.lease, user):
            raise PermissionDenied("Current payer authority is required.")
    if not hasattr(attempt, "paymob_payment"):
        raise RentalConflict("This payment has no hosted session.")
    with transaction.atomic():
        payment = PaymobPayment.objects.select_for_update().get(attempt=attempt)
        attempt.refresh_from_db()
        session = CheckoutSession.objects.select_for_update().get(attempt=attempt)
        if attempt.payment_status != "pending" or payment.status in {
            "renewing",
            "review",
        }:
            return attempt
        recovering = payment.status == "renewal_unknown"
        if not recovering and session.expires_at > timezone.now():
            return attempt
        if not client.sandbox_ready() or not session.hosted_url or not payment.order_id:
            raise client.PaymobUnavailable()
        if recovering:
            record = None
        else:
            record = _start_renewal(user, attempt, session, payment, key)
            if record is None:
                return attempt
    redirect = (
        session.navigation["return_url"]
        + "?"
        + urlencode(
            {"state": session.return_state, "payment_attempt_id": str(attempt.id)}
        )
    )
    try:
        if recovering:
            transactions = client.order_transactions(payment)
            if transactions:
                for item in transactions:
                    apply_snapshot(payment, client.inquiry(payment, str(item["id"])))
                return PaymentAttempt.objects.select_related(
                    "invoice", "quote", "paymob_payment", "checkout_session"
                ).get(pk=attempt.pk)
            response = client.retrieve_intention(payment)
            expiry = verified_expiry(
                response, payment, session, redirect, allow_expired=True
            )
            _save_session(payment, session, response, expiry, "renewal_unknown")
            IdempotencyRecord.objects.filter(
                user=user,
                operation__startswith=f"payment.resume.{attempt.id}.",
                recovery_status="unknown",
            ).update(recovery_status="confirmed")
            # GET resolved the earlier PUT against the original, transaction-free
            # intention. An expired verified key can now follow normal renewal;
            # an unreadable/ambiguous response above can never reach another PUT.
            if expiry <= timezone.now():
                with transaction.atomic():
                    payment = PaymobPayment.objects.select_for_update().get(
                        pk=payment.pk
                    )
                    attempt.refresh_from_db()
                    session.refresh_from_db()
                    if (
                        payment.status == "ready"
                        and attempt.payment_status == "pending"
                        and session.expires_at <= timezone.now()
                    ):
                        record = _start_renewal(user, attempt, session, payment, key)
                if record is not None:
                    _renew(payment, attempt, session, redirect, record)
        else:
            _renew(payment, attempt, session, redirect, record)
    except Exception:
        if record is not None:
            PaymobPayment.objects.filter(pk=payment.pk, status="renewing").update(
                status="renewal_unknown", failure_code="renewal_unknown"
            )
            IdempotencyRecord.objects.filter(pk=record.pk).update(
                recovery_status="unknown"
            )
        raise client.PaymobUnavailable() from None
    return PaymentAttempt.objects.select_related(
        "invoice", "quote", "paymob_payment", "checkout_session"
    ).get(pk=attempt.pk)


def _start_renewal(user, attempt, session, payment, key):
    operation = f"payment.resume.{attempt.id}.{int(session.expires_at.timestamp())}"
    record, created = IdempotencyRecord.objects.get_or_create(
        user=user,
        operation=operation,
        request_key=key,
        defaults={"fingerprint": "resume", "recovery_status": "pending"},
    )
    if not created:
        return None
    payment.status = "renewing"
    payment.save(update_fields=["status", "updated_at"])
    return record


def _renew(payment, attempt, session, redirect, record):
    transactions = client.order_transactions(payment)
    if transactions:
        # Resolve existing financial activity; never renew around authorization.
        for item in transactions:
            snapshot = client.inquiry(payment, str(item["id"]))
            apply_snapshot(payment, snapshot)
        PaymobPayment.objects.filter(pk=payment.pk, status="renewing").update(
            status="ready"
        )
    else:
        response = client.renew_intention(payment, redirect)
        expiry = verified_expiry(response, payment, session, redirect)
        _save_session(payment, session, response, expiry, "renewing")
    IdempotencyRecord.objects.filter(pk=record.pk).update(recovery_status="confirmed")


def _save_session(payment, session, response, expiry, expected_status):
    with transaction.atomic():
        current = PaymobPayment.objects.select_for_update().get(pk=payment.pk)
        if current.status == expected_status:
            CheckoutSession.objects.filter(pk=session.pk).update(
                expires_at=expiry,
                hosted_url=client.checkout_url(response.get("client_secret")),
            )
            current.status = "ready"
            current.failure_code = ""
            current.save(update_fields=["status", "failure_code", "updated_at"])
