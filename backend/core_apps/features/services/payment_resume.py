"""Resume one original hosted payment. Never create a replacement intention."""

import base64
import json
import uuid
from datetime import datetime, timezone as datetime_timezone
from urllib.parse import urlencode
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..models import CheckoutSession, IdempotencyRecord, PaymentAttempt, PaymobPayment
from . import paymob_client as client
from .paymob_payments import apply_snapshot
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
            "renewal_unknown",
            "review",
        }:
            return attempt
        if session.expires_at > timezone.now():
            return attempt
        if not client.sandbox_ready() or not session.hosted_url or not payment.order_id:
            raise client.PaymobUnavailable()
        operation = f"payment.resume.{attempt.id}.{int(session.expires_at.timestamp())}"
        record, created = IdempotencyRecord.objects.get_or_create(
            user=user,
            operation=operation,
            request_key=key,
            defaults={"fingerprint": "resume", "recovery_status": "pending"},
        )
        if not created:
            return attempt
        payment.status = "renewing"
        payment.save(update_fields=["status", "updated_at"])
    try:
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
            redirect = (
                session.navigation["return_url"]
                + "?"
                + urlencode(
                    {
                        "state": session.return_state,
                        "payment_attempt_id": str(attempt.id),
                    }
                )
            )
            response = client.renew_intention(payment, redirect)
            detail = response.get("intention_detail", {})
            if (
                response.get("id") != payment.intention_id
                or str(response.get("intention_order_id")) != payment.order_id
                or response.get("special_reference") != payment.reference
                or detail.get("amount") != attempt.amount_minor
                or detail.get("currency") != attempt.currency
            ):
                raise client.PaymobUnavailable()
            expiries = []
            for item in response.get("payment_keys", []):
                encoded = item.get("key", "").split(".")
                if len(encoded) != 3:
                    continue
                claims = json.loads(
                    base64.urlsafe_b64decode(encoded[1] + "=" * (-len(encoded[1]) % 4))
                )
                if (
                    claims.get("redirection_url") != redirect
                    or str(claims.get("order_id")) != payment.order_id
                    or claims.get("amount_cents") != attempt.amount_minor
                    or claims.get("currency") != attempt.currency
                    or str(claims.get("integration_id")) != payment.integration_id
                ):
                    raise client.PaymobUnavailable()
                expiries.append(
                    datetime.fromtimestamp(int(claims["exp"]), datetime_timezone.utc)
                )
            if not expiries or min(expiries) <= timezone.now():
                raise client.PaymobUnavailable()
            with transaction.atomic():
                current = PaymobPayment.objects.select_for_update().get(pk=payment.pk)
                if current.status == "renewing":
                    CheckoutSession.objects.filter(pk=session.pk).update(
                        expires_at=min(expiries),
                        hosted_url=client.checkout_url(response.get("client_secret")),
                    )
                    current.status = "ready"
                    current.save(update_fields=["status", "updated_at"])
        IdempotencyRecord.objects.filter(pk=record.pk).update(
            recovery_status="confirmed"
        )
    except Exception:
        PaymobPayment.objects.filter(pk=payment.pk, status="renewing").update(
            status="renewal_unknown", failure_code="renewal_unknown"
        )
        IdempotencyRecord.objects.filter(pk=record.pk).update(recovery_status="unknown")
        raise client.PaymobUnavailable() from None
    return PaymentAttempt.objects.select_related(
        "invoice", "quote", "paymob_payment", "checkout_session"
    ).get(pk=attempt.pk)
