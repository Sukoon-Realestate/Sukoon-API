"""Rental phase3 views: owner payables."""

import hashlib
import json
import secrets
import uuid
from urllib.parse import urlparse
from django.conf import settings
from django.db import transaction
from rest_framework.decorators import (
    api_view,
    permission_classes,
    renderer_classes,
    throttle_classes,
)
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import (
    IdempotencyRecord,
    OwnerPayable,
    PaymentAttempt,
    ProviderWebhookEvent,
)
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict
from ..services.rental_phase3 import payment_attempt_payload, process_provider_event
from .rent_invoice_quote import (
    PaymentReconcileThrottle,
    _money,
    _attempt,
    _active_session,
    _invoice,
    can_pay,
)


def _validated_navigation(invoice, attempt):
    origins = list(getattr(settings, "RENTAL_CHECKOUT_ALLOWED_ORIGINS", []))
    if any(
        urlparse(origin).scheme != "https" or urlparse(origin).path not in {"", "/"}
        for origin in origins
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


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payment_attempts(request):
    data = request.data if request.method == "POST" else request.query_params
    invoice_id = data.get("invoice_id")
    request_key = data.get("request_key")
    if not invoice_id or not request_key:
        raise ValidationError("invoice_id and request_key are required for recovery.")
    try:
        invoice_id, request_key = str(uuid.UUID(str(invoice_id))), str(
            uuid.UUID(str(request_key))
        )
    except ValueError:
        raise ValidationError("invoice_id and request_key must be UUIDs.")
    from ..services.billing_invoices import authorized_invoice
    from ..services.rental_foundation import private_no_store

    with transaction.atomic():
        if request.method == "POST":
            if data.get("action") != "resolve_checkout":
                raise ValidationError({"action": "Must be resolve_checkout."})
            # The same company/property, lease and invoice locks serialize this
            # closure against checkout. GET absence never closes an operation.
            invoice = _invoice(request, invoice_id, lock=True)
            if not can_pay(invoice.lease, request.user):
                raise PermissionDenied(
                    "Current authority to recover this checkout is required."
                )
        else:
            invoice = authorized_invoice(request.user, invoice_id)
        return private_no_store(
            Response(_checkout_recovery(request, invoice, request_key))
        )


def _checkout_recovery(request, invoice, request_key):
    attempts = list(
        PaymentAttempt.objects.filter(
            invoice=invoice, payer=request.user, request_key=request_key
        ).select_related("quote")
    )
    operation = f"invoice.checkout.{invoice.id}"
    record = IdempotencyRecord.objects.filter(
        user=request.user, operation=operation, request_key=request_key
    ).first()
    if request.method == "POST" and not attempts and record is None:
        record = IdempotencyRecord.objects.create(
            user=request.user,
            operation=operation,
            request_key=request_key,
            fingerprint="",
            response_data={"code": "operation_closed_without_execution"},
            response_status=409,
            is_rental_operation=True,
            request_subject_id=invoice.id,
            result_subject_id=invoice.id,
            result_revision=invoice.revision,
            recovery_status=IdempotencyRecord.RecoveryStatus.ABSENT_FINAL,
        )
    return {
        "invoice_id": str(invoice.id),
        "request_key": request_key,
        "results": [payment_attempt_payload(x, request.user) for x in attempts],
        "absence_confirmed": bool(
            not attempts
            and record
            and record.recovery_status == IdempotencyRecord.RecoveryStatus.ABSENT_FINAL
        ),
        "active_session": _active_session(attempts[0]) if attempts else None,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payment_attempt_detail(request, attempt_id):
    return Response(
        payment_attempt_payload(_attempt(request, attempt_id), request.user)
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
@throttle_classes([PaymentReconcileThrottle])
def payment_attempt_reconcile(request, attempt_id):
    with transaction.atomic():
        attempt = _attempt(request, attempt_id, lock=True)
        if request.user != attempt.payer:
            raise PermissionDenied("Only the payer can reconcile this attempt.")
        if (
            request.data.get("action") or request.data.get("decision")
        ) != "reconcile" or int(
            request.data.get("expected_revision", 0)
        ) != attempt.revision:
            raise RentalConflict(
                "Payment attempt revision or action is invalid.", code="stale_revision"
            )
        return Response(payment_attempt_payload(attempt, request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def owner_payables(request):
    if request.query_params.get("workspace") != "owner":
        raise ValidationError({"workspace": "Must be owner."})
    from django.db.models import Q

    queryset = OwnerPayable.objects.filter(
        Q(invoice__beneficiary=request.user)
        | Q(invoice__beneficiary__isnull=True, lease__owner=request.user)
    ).select_related("lease", "invoice")
    if request.query_params.get("lease_id"):
        queryset = queryset.filter(lease__id=request.query_params["lease_id"])
    results = [
        {
            "id": str(item.id),
            "lease_id": str(item.lease.id),
            "invoice_id": str(item.invoice.id),
            "revision": item.revision,
            "gross": _money(item.gross_minor),
            "commission": _money(item.commission_minor),
            "processing_fee": _money(item.processing_fee_minor),
            "net": _money(item.net_minor),
            "settlement_status": item.settlement_status,
            "payout_status": item.payout_status,
            "blocking_reasons": item.blocking_reasons,
        }
        for item in queryset.order_by("-created_at")
    ]
    return Response(
        {"count": len(results), "next": None, "previous": None, "results": results}
    )


def apply_fake_payment_event(payload):
    try:
        attempt = PaymentAttempt.objects.get(id=payload.get("payment_attempt_id"))
    except (PaymentAttempt.DoesNotExist, ValueError):
        raise NotFound()
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    event, created = ProviderWebhookEvent.objects.get_or_create(
        provider="fake",
        provider_event_id=str(payload.get("event_id")),
        defaults={
            "event_type": payload.get("type", ""),
            "payment_attempt": attempt,
            "sequence": int(payload.get("sequence", 0)),
            "payload_digest": hashlib.sha256(canonical).hexdigest(),
            "signature_valid": True,
            "payload": payload,
        },
    )
    if not created and event.payload_digest != hashlib.sha256(canonical).hexdigest():
        raise RentalConflict("Provider event ID was reused with different content.")
    process_provider_event(event)
    return {"status": "accepted", "duplicate": not created}
