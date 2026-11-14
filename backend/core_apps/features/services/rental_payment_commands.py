"""Financial commands preserve original locks, receipts, authority and provider boundaries."""

import uuid
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.features.models import PaymentAttempt, PaymentQuote, RentInvoice
from core_apps.features.providers import checkout_available
from core_apps.features.services.rental_phase2 import (
    RentalConflict,
    remember_mutation,
    replay_operation,
)
from core_apps.features.services.rental_phase3 import (
    invoice_payment_allowed,
    quote_fingerprint,
)
from core_apps.features.services.company.tenancy_access import can_pay
from django.db import IntegrityError
from core_apps.features.models import CheckoutSession
from core_apps.features.providers import (
    mock_completion_metadata,
    fake_provider_available,
    get_rental_provider,
)
import secrets
from urllib.parse import urlparse
from .money_result import MoneyResult
from .money_access import rental_invoice_for
from .money_projection import _money, quote_payload
from core_apps.common.command_authority import recheck_actor_session
from .payment_events import apply_fake_payment_event


def quote_rent(actor, claims, data, proof, invoice_id):
    expected = data.get("expected_revision")
    request_key = data.get("request_key")
    if expected is None or not request_key:
        raise ValidationError(
            {"request_key": "request_key and expected_revision are required."}
        )
    try:
        expected = int(expected)
        request_key = uuid.UUID(str(request_key))
    except (ValueError, TypeError):
        raise ValidationError({"request_key": "Must be a UUID."})
    with transaction.atomic():
        invoice = rental_invoice_for(actor, invoice_id, lock=True)
        recheck_actor_session(actor, claims)
        if not can_pay(invoice.lease, actor):
            raise PermissionDenied("Current authority to pay this invoice is required.")
        replay = replay_operation(
            actor, f"invoice.quote.{invoice_id}", request_key, data
        )
        if replay:
            return MoneyResult(replay[0], status=replay[1])
        if not checkout_available():
            raise PermissionDenied(
                {
                    "message": "Secure checkout is unavailable.",
                    "code": "capability_unavailable",
                }
            )
        if int(expected) != invoice.revision:
            raise RentalConflict("Invoice revision conflict.", code="stale_revision")
        if not invoice_payment_allowed(actor, invoice):
            raise RentalConflict("This invoice is not payable.")
        from ..services.chargebacks.funding import quote_amount

        balance = quote_amount(invoice)
        if not balance or invoice.status not in {
            RentInvoice.Status.DUE,
            RentInvoice.Status.OVERDUE,
            RentInvoice.Status.PARTIALLY_PAID,
        }:
            raise RentalConflict("This invoice is not payable.")
        expires = timezone.now() + timedelta(minutes=settings.RENTAL_QUOTE_TTL_MINUTES)
        quote = PaymentQuote.objects.create(
            invoice=invoice,
            request_key=request_key,
            invoice_revision=invoice.revision,
            payer_amount_minor=balance,
            policy_version="rental-policy-v1",
            fingerprint=quote_fingerprint(invoice, request_key, balance, expires),
            expires_at=expires,
        )
        output = remember_mutation(
            user=actor,
            operation=f"invoice.quote.{invoice_id}",
            request_key=request_key,
            payload=data,
            request_subject_id=invoice.id,
            result_subject_id=quote.id,
            result_revision=invoice.revision,
            resource=quote_payload(quote),
            response_status=201,
        )
    return MoneyResult(output, status=status.HTTP_201_CREATED)


def checkout_rent(actor, claims, data, proof, invoice_id):
    from ..rental_serializers_parts.command_serializers import (
        RentCheckoutCommand,
        validated,
    )

    required = {"invoice_id", "quote_id", "expected_revision", "request_key"}
    if not hasattr(data, "get") or not required.issubset(data):
        raise ValidationError({"request": f"Required: {', '.join(sorted(required))}."})
    command = validated(RentCheckoutCommand, data)
    if str(command["invoice_id"]) != str(invoice_id):
        raise ValidationError({"invoice_id": "Must match the path invoice."})
    request_key = command["request_key"]
    quote_id = command["quote_id"]
    expected_revision = command["expected_revision"]
    from ..services.paymob_client import checkout_ready
    from ..models import PaymobPayment

    if (
        checkout_ready()
        or PaymobPayment.objects.filter(
            attempt__invoice__id=invoice_id,
            attempt__payer=actor,
            attempt__request_key=request_key,
        ).exists()
    ):
        from ..services.paymob_payments import checkout, rental_response

        attempt = checkout(
            actor,
            invoice_id,
            {
                **data,
                "request_key": request_key,
                "quote_id": quote_id,
                "expected_revision": expected_revision,
            },
            rental=True,
        )
        return MoneyResult(rental_response(attempt), status=status.HTTP_201_CREATED)
    operation = f"invoice.checkout.{invoice_id}"
    with transaction.atomic():
        invoice = rental_invoice_for(actor, invoice_id, lock=True)
        recheck_actor_session(actor, claims)
        if not can_pay(invoice.lease, actor):
            raise PermissionDenied("Current authority to pay this invoice is required.")
        if not checkout_available():
            return MoneyResult(
                {
                    "message": "Secure checkout is unavailable.",
                    "code": "capability_unavailable",
                    "subject_id": str(invoice.id),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        replay = replay_operation(actor, operation, request_key, data)
        if replay:
            return MoneyResult(replay[0], status=replay[1])
        recheck_actor_session(actor, claims)
        if not invoice_payment_allowed(actor, invoice):
            raise RentalConflict("This invoice is not payable.")
        quote = get_object_or_404(
            PaymentQuote.objects.select_for_update(), id=quote_id, invoice=invoice
        )
        if (
            expected_revision != invoice.revision
            or quote.invoice_revision != invoice.revision
        ):
            raise RentalConflict("Invoice revision conflict.", code="stale_revision")
        if quote.expires_at <= timezone.now():
            raise RentalConflict("The payment quote expired.", code="quote_expired")
        from ..services.chargebacks.funding import quote_amount

        if quote.payer_amount_minor != quote_amount(invoice):
            raise RentalConflict(
                "The quote no longer matches the invoice.", code="document_changed"
            )
        try:
            with transaction.atomic():
                attempt = PaymentAttempt.objects.create(
                    invoice=invoice,
                    payer=actor,
                    quote=quote,
                    request_key=request_key,
                    invoice_revision=invoice.revision,
                    policy_version=quote.policy_version,
                    quote_fingerprint=quote.fingerprint,
                    amount_minor=quote.payer_amount_minor,
                    payment_status=PaymentAttempt.Status.PENDING,
                )
        except IntegrityError:
            raise RentalConflict(
                "This invoice already has a live payment attempt.",
                code="payment_in_progress",
            )
        provider = get_rental_provider().create_checkout_session(
            attempt.id, request_key
        )
        navigation = _validated_navigation(invoice, attempt)
        expires = timezone.now() + timedelta(
            minutes=settings.RENTAL_CHECKOUT_TTL_MINUTES
        )
        session = CheckoutSession.objects.create(
            invoice=invoice,
            payer=actor,
            attempt=attempt,
            quote=quote,
            request_key=request_key,
            hosted_url=provider.hosted_url,
            provider_session_id=provider.provider_session_id,
            expires_at=expires,
            status="created",
            navigation=navigation,
            return_state=navigation["return_state"],
        )
        auto_captured = fake_provider_available() and getattr(
            settings, "RENTAL_FAKE_AUTO_CAPTURE", False
        )
        if auto_captured:
            apply_fake_payment_event(
                {
                    "event_id": f"mock-checkout:{attempt.id}:{request_key}",
                    "type": "payment.captured",
                    "sequence": attempt.revision,
                    "payment_attempt_id": str(attempt.id),
                    "amount_minor": attempt.amount_minor,
                    "currency": attempt.currency,
                }
            )
            attempt.refresh_from_db()
            session.status = "completed"
            session.save(update_fields=["status", "updated_at"])
        resource = {
            "session_id": str(session.id),
            **mock_completion_metadata(
                "payment-attempts", attempt.id, attempt.revision
            ),
            "payment_attempt_id": str(attempt.id),
            "invoice_id": str(invoice.id),
            "quote_id": str(quote.id),
            "invoice_revision": invoice.revision,
            "request_key": str(request_key),
            "status": "captured" if auto_captured else "created",
            "amount": _money(attempt.amount_minor),
            "checkout_url": session.hosted_url,
            "expires_at": expires.isoformat(),
            "navigation": navigation,
        }
        output = remember_mutation(
            user=actor,
            operation=operation,
            request_key=request_key,
            payload=data,
            request_subject_id=invoice.id,
            result_subject_id=session.id,
            result_revision=attempt.revision,
            resource=resource,
            response_status=201,
        )
    return MoneyResult(output, status=status.HTTP_201_CREATED)


def _validated_navigation(invoice, attempt):
    origins = list(getattr(settings, "RENTAL_CHECKOUT_ALLOWED_ORIGINS", []))
    if any(
        (
            urlparse(origin).scheme != "https" or urlparse(origin).path not in {"", "/"}
            for origin in origins
        )
    ):
        raise ValidationError("Checkout origins must be exact HTTPS origins.")
    return_url = settings.RENTAL_CHECKOUT_RETURN_URL.format(invoice_id=invoice.id)
    if urlparse(return_url).scheme != "https":
        raise ValidationError("Checkout return URL must use HTTPS.")
    return {
        "allowed_origins": origins,
        "return_url": return_url,
        "return_state": secrets.token_urlsafe(32),
        "payment_attempt_id": str(attempt.id),
        "external_schemes": list(
            getattr(settings, "RENTAL_CHECKOUT_EXTERNAL_SCHEMES", [])
        ),
    }


__all__ = ["checkout_rent", "quote_rent"]
