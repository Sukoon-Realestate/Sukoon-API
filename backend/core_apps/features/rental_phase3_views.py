import hashlib
import json
import secrets
import uuid
from datetime import timedelta
from urllib.parse import urlparse

from django.conf import settings
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    renderer_classes,
    throttle_classes,
)
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from .models import (
    CheckoutSession,
    OwnerPayable,
    PaymentAttempt,
    PaymentQuote,
    ProviderWebhookEvent,
    RentInvoice,
)
from .providers import fake_provider_available, get_rental_provider, verify_fake_webhook
from .renderers import FeatureJsonRenderer
from .services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .services.rental_phase3 import (
    invoice_balance_minor,
    payment_attempt_payload,
    process_provider_event,
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
        queryset = queryset.select_for_update()
    invoice = get_object_or_404(queryset, id=invoice_id)
    if request.user not in (invoice.lease.owner, invoice.lease.tenant):
        raise NotFound()
    return invoice


def _attempt(request, attempt_id, lock=False):
    queryset = PaymentAttempt.objects.select_related("invoice__lease", "quote")
    if lock:
        queryset = queryset.select_for_update()
    attempt = get_object_or_404(queryset, id=attempt_id)
    if request.user not in (attempt.invoice.lease.owner, attempt.invoice.lease.tenant):
        raise NotFound()
    return attempt


def _active_session(attempt):
    session = getattr(attempt, "checkout_session", None)
    if (
        not session
        or session.expires_at <= timezone.now()
        or session.status not in {"created", "pending"}
    ):
        return None
    return {
        "session_id": str(session.id),
        "checkout_url": session.hosted_url,
        "expires_at": session.expires_at.isoformat(),
        "navigation": session.navigation,
    }


def quote_payload(quote):
    return {
        "quote_id": str(quote.id),
        "invoice_id": str(quote.invoice_id),
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
        request_key = uuid.UUID(str(request_key))
    except ValueError:
        raise ValidationError({"request_key": "Must be a UUID."})
    replay = replay_operation(
        request.user, f"invoice.quote.{invoice_id}", request_key, request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        invoice = _invoice(request, invoice_id, lock=True)
        if request.user != invoice.lease.tenant:
            raise PermissionDenied("Only the tenant can quote this invoice.")
        if not getattr(settings, "RENTAL_CHECKOUT_ENABLED", False):
            raise PermissionDenied(
                {
                    "message": "Secure checkout is unavailable.",
                    "code": "capability_unavailable",
                }
            )
        if int(expected) != invoice.revision:
            raise RentalConflict("Invoice revision conflict.", code="stale_revision")
        balance = invoice_balance_minor(invoice)
        if not balance or invoice.status not in {
            RentInvoice.Status.DUE,
            RentInvoice.Status.OVERDUE,
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
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        invoice = _invoice(request, invoice_id, lock=True)
        if request.user != invoice.lease.tenant:
            raise PermissionDenied("Only the tenant can pay this invoice.")
        if not getattr(settings, "RENTAL_CHECKOUT_ENABLED", False):
            return Response(
                {
                    "message": "Secure checkout is unavailable.",
                    "code": "capability_unavailable",
                    "subject_id": str(invoice.id),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
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
        resource = {
            "session_id": str(session.id),
            "payment_attempt_id": str(attempt.id),
            "invoice_id": str(invoice.id),
            "quote_id": str(quote.id),
            "invoice_revision": invoice.revision,
            "request_key": str(request_key),
            "status": "created",
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
            result_subject_id=attempt.id,
            result_revision=attempt.revision,
            resource=resource,
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payment_attempts(request):
    invoice_id = request.query_params.get("invoice_id")
    request_key = request.query_params.get("request_key")
    if not invoice_id or not request_key:
        raise ValidationError("invoice_id and request_key are required for recovery.")
    invoice = _invoice(request, invoice_id)
    attempts = list(
        PaymentAttempt.objects.filter(
            invoice=invoice, payer=request.user, request_key=request_key
        ).select_related("quote")
    )
    active = _active_session(attempts[0]) if attempts else None
    return Response(
        {
            "invoice_id": str(invoice.id),
            "request_key": request_key,
            "results": [payment_attempt_payload(x) for x in attempts],
            "absence_confirmed": not attempts,
            "active_session": active,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payment_attempt_detail(request, attempt_id):
    return Response(payment_attempt_payload(_attempt(request, attempt_id)))


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
            request.data.get("action") != "reconcile"
            or int(request.data.get("expected_revision", 0)) != attempt.revision
        ):
            raise RentalConflict(
                "Payment attempt revision or action is invalid.", code="stale_revision"
            )
        return Response(payment_attempt_payload(attempt))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def owner_payables(request):
    if request.query_params.get("workspace") != "owner":
        raise ValidationError({"workspace": "Must be owner."})
    queryset = OwnerPayable.objects.filter(lease__owner=request.user).select_related(
        "lease", "invoice"
    )
    if request.query_params.get("lease_id"):
        queryset = queryset.filter(lease_id=request.query_params["lease_id"])
    results = [
        {
            "id": str(item.id),
            "lease_id": str(item.lease_id),
            "invoice_id": str(item.invoice_id),
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


@api_view(["POST"])
@permission_classes([AllowAny])
@renderer_classes([FeatureJsonRenderer])
def fake_payment_webhook(request):
    if not fake_provider_available():
        raise NotFound()
    if not verify_fake_webhook(request.data, request.headers.get("X-Rental-Signature")):
        raise PermissionDenied("Invalid provider signature.")
    try:
        attempt = PaymentAttempt.objects.get(id=request.data.get("payment_attempt_id"))
    except (PaymentAttempt.DoesNotExist, ValueError):
        raise NotFound()
    canonical = json.dumps(request.data, sort_keys=True, separators=(",", ":")).encode()
    event, created = ProviderWebhookEvent.objects.get_or_create(
        provider="fake",
        provider_event_id=str(request.data.get("event_id")),
        defaults={
            "event_type": request.data.get("type", ""),
            "payment_attempt": attempt,
            "sequence": int(request.data.get("sequence", 0)),
            "payload_digest": hashlib.sha256(canonical).hexdigest(),
            "signature_valid": True,
            "payload": request.data,
        },
    )
    if not created and event.payload_digest != hashlib.sha256(canonical).hexdigest():
        raise RentalConflict("Provider event ID was reused with different content.")
    process_provider_event(event)
    return Response({"status": "accepted", "duplicate": not created})
