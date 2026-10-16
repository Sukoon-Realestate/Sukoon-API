"""Rental phase3 views: rent invoice quote."""

import uuid
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from ..models import Lease, IdempotencyRecord, PaymentAttempt, PaymentQuote, RentInvoice
from ..providers import checkout_available
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from ..services.rental_phase3 import (
    invoice_balance_minor,
    invoice_payment_allowed,
    quote_fingerprint,
)


class PaymentReconcileThrottle(UserRateThrottle):
    rate = "6/min"


def _money(amount, currency="EGP", exponent=2):
    return {"amount_minor": amount, "currency": currency, "exponent": exponent}


def _invoice(request, invoice_id, lock=False):
    queryset = RentInvoice.objects.select_related(
        "lease", "lease__property", "billing_period"
    )
    if lock:
        candidate = get_object_or_404(queryset, id=invoice_id)
        if candidate.lease_id is None:
            raise NotFound()
        from core_apps.properties.models import Property

        Property.objects.select_for_update().get(pk=candidate.lease.property_id)
        Lease.objects.select_for_update().get(pk=candidate.lease_id)
        queryset = queryset.select_for_update(of=("self",))
    invoice = get_object_or_404(queryset, id=invoice_id)
    if invoice.lease_id is None or request.user not in (
        invoice.lease.owner,
        invoice.lease.tenant,
    ):
        raise NotFound()
    return invoice


def _attempt(request, attempt_id, lock=False):
    queryset = PaymentAttempt.objects.select_related("invoice__lease", "quote")
    if lock:
        candidate = get_object_or_404(queryset, id=attempt_id)
        if candidate.invoice.lease_id is not None:
            from core_apps.properties.models import Property

            Property.objects.select_for_update().get(
                pk=candidate.invoice.lease.property_id
            )
            Lease.objects.select_for_update().get(pk=candidate.invoice.lease_id)
        queryset = queryset.select_for_update(of=("self",))
    attempt = get_object_or_404(queryset, id=attempt_id)
    if attempt.invoice.lease_id is None:
        if request.user.pk != attempt.payer_id:
            raise NotFound()
        return attempt
    if request.user not in (attempt.invoice.lease.owner, attempt.invoice.lease.tenant):
        raise NotFound()
    return attempt


def _active_session(attempt):
    session = getattr(attempt, "checkout_session", None)
    if (
        not session
        or session.expires_at <= timezone.now()
        or session.status not in {"created", "pending"}
        or attempt.payment_status not in {"created", "pending"}
    ):
        return None
    receipt = IdempotencyRecord.objects.filter(
        user=attempt.payer,
        operation=f"invoice.checkout.{attempt.invoice.id}",
        request_key=str(attempt.request_key),
        result_subject_id=session.id,
    ).first()
    if not receipt:
        return None
    resource = receipt.response_data.get("resource", {})
    if resource.get("session_id") != str(session.id) or resource.get(
        "payment_attempt_id"
    ) != str(attempt.id):
        return None
    return {**resource, "operation_receipt_id": str(receipt.id)}


def quote_payload(quote):
    return {
        "quote_id": str(quote.id),
        "invoice_id": str(quote.invoice.id),
        "invoice_revision": quote.invoice_revision,
        "payer_amount": _money(
            quote.payer_amount_minor, quote.currency, quote.exponent
        ),
        "tenant_service_fee": _money(
            quote.tenant_service_fee_minor, quote.currency, quote.exponent
        ),
        "policy_version": quote.policy_version,
        "fingerprint": quote.fingerprint,
        "expires_at": quote.expires_at.isoformat(),
    }


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rent_invoice_quote(request, invoice_id):
    expected = request.data.get("expected_revision")
    request_key = request.data.get("request_key")
    if expected is None or not request_key:
        raise ValidationError(
            {"request_key": "request_key and expected_revision are required."}
        )
    try:
        expected = int(expected)
        request_key = uuid.UUID(str(request_key))
    except (ValueError, TypeError):
        raise ValidationError({"request_key": "Must be a UUID."})
    replay = replay_operation(
        request.user, f"invoice.quote.{invoice_id}", request_key, request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        invoice = _invoice(request, invoice_id, lock=True)
        replay = replay_operation(
            request.user, f"invoice.quote.{invoice_id}", request_key, request.data
        )
        if replay:
            return Response(replay[0], status=replay[1])
        if request.user != invoice.lease.tenant:
            raise PermissionDenied("Only the tenant can quote this invoice.")
        if not checkout_available():
            raise PermissionDenied(
                {
                    "message": "Secure checkout is unavailable.",
                    "code": "capability_unavailable",
                }
            )
        if int(expected) != invoice.revision:
            raise RentalConflict("Invoice revision conflict.", code="stale_revision")
        if not invoice_payment_allowed(request.user, invoice):
            raise RentalConflict("This invoice is not payable.")
        balance = invoice_balance_minor(invoice)
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
            user=request.user,
            operation=f"invoice.quote.{invoice_id}",
            request_key=request_key,
            payload=request.data,
            request_subject_id=invoice.id,
            result_subject_id=quote.id,
            result_revision=invoice.revision,
            resource=quote_payload(quote),
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)
