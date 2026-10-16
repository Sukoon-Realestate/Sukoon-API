"""Rental phase3 views: rent invoice checkout."""

import uuid
from datetime import timedelta
from django.conf import settings
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from ..models import CheckoutSession, PaymentAttempt, PaymentQuote
from ..providers import (
    mock_completion_metadata,
    checkout_available,
    fake_provider_available,
    get_rental_provider,
    verify_fake_webhook,
)
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from ..services.rental_phase3 import invoice_balance_minor, invoice_payment_allowed
from .rent_invoice_quote import _money, _invoice
from .owner_payables import _validated_navigation, apply_fake_payment_event


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rent_invoice_checkout(request, invoice_id):
    required = {"invoice_id", "quote_id", "expected_revision", "request_key"}
    if not required.issubset(request.data):
        raise ValidationError({"request": f"Required: {', '.join(sorted(required))}."})
    if str(request.data["invoice_id"]) != str(invoice_id):
        raise ValidationError({"invoice_id": "Must match the path invoice."})
    try:
        request_key = uuid.UUID(str(request.data["request_key"]))
        quote_id = uuid.UUID(str(request.data["quote_id"]))
    except ValueError:
        raise ValidationError("quote_id and request_key must be UUIDs.")
    operation = f"invoice.checkout.{invoice_id}"
    _invoice(
        request, invoice_id
    )  # Reauthorize before returning any historical receipt.
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        invoice = _invoice(request, invoice_id, lock=True)
        if request.user != invoice.lease.tenant:
            raise PermissionDenied("Only the tenant can pay this invoice.")
        if not checkout_available():
            return Response(
                {
                    "message": "Secure checkout is unavailable.",
                    "code": "capability_unavailable",
                    "subject_id": str(invoice.id),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        if not invoice_payment_allowed(request.user, invoice):
            raise RentalConflict("This invoice is not payable.")
        quote = get_object_or_404(
            PaymentQuote.objects.select_for_update(), id=quote_id, invoice=invoice
        )
        if (
            int(request.data["expected_revision"]) != invoice.revision
            or quote.invoice_revision != invoice.revision
        ):
            raise RentalConflict("Invoice revision conflict.", code="stale_revision")
        if quote.expires_at <= timezone.now():
            raise RentalConflict("The payment quote expired.", code="quote_expired")
        if quote.payer_amount_minor != invoice_balance_minor(invoice):
            raise RentalConflict(
                "The quote no longer matches the invoice.", code="document_changed"
            )
        try:
            with transaction.atomic():
                attempt = PaymentAttempt.objects.create(
                    invoice=invoice,
                    payer=request.user,
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
            payer=request.user,
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
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=invoice.id,
            result_subject_id=session.id,
            result_revision=attempt.revision,
            resource=resource,
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
@renderer_classes([FeatureJsonRenderer])
def fake_payment_webhook(request):
    if not fake_provider_available():
        raise NotFound()
    if not verify_fake_webhook(request.data, request.headers.get("X-Rental-Signature")):
        raise PermissionDenied("Invalid provider signature.")
    return Response(apply_fake_payment_event(request.data))
