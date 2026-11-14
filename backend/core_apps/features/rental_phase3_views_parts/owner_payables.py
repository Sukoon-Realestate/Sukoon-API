"""Rental phase3 views: owner payables."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


import secrets
import uuid
from urllib.parse import urlparse
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import IdempotencyRecord, OwnerPayable, PaymentAttempt
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict
from ..services.rental_phase3 import payment_attempt_payload
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


class PaymentAttemptsView(FeatureAPIView):
    name = "Payment Attempts"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "owner_payables",
            "payment_attempts",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "owner_payables",
            "payment_attempts",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        data = request.data if request.method == "POST" else request.query_params
        invoice_id = data.get("invoice_id")
        request_key = data.get("request_key")
        if not invoice_id or not request_key:
            raise ValidationError(
                "invoice_id and request_key are required for recovery."
            )
        try:
            invoice_id, request_key = str(uuid.UUID(str(invoice_id))), str(
                uuid.UUID(str(request_key))
            )
        except ValueError:
            raise ValidationError("invoice_id and request_key must be UUIDs.")
        from ..services.billing_invoices import authorized_invoice
        from ..services.rental_foundation import private_no_store

        with transaction.atomic():
            invoice = authorized_invoice(request.user, invoice_id)
            return private_no_store(
                Response(_checkout_recovery(request, invoice, request_key))
            )

    def post(self, request):
        data = request.data if request.method == "POST" else request.query_params
        invoice_id = data.get("invoice_id")
        request_key = data.get("request_key")
        if not invoice_id or not request_key:
            raise ValidationError(
                "invoice_id and request_key are required for recovery."
            )
        try:
            invoice_id, request_key = str(uuid.UUID(str(invoice_id))), str(
                uuid.UUID(str(request_key))
            )
        except ValueError:
            raise ValidationError("invoice_id and request_key must be UUIDs.")
        from ..services.rental_foundation import private_no_store

        with transaction.atomic():
            if data.get("action") != "resolve_checkout":
                raise ValidationError({"action": "Must be resolve_checkout."})
            invoice = _invoice(request, invoice_id, lock=True)
            if not can_pay(invoice.lease, request.user):
                raise PermissionDenied(
                    "Current authority to recover this checkout is required."
                )
            return private_no_store(
                Response(_checkout_recovery(request, invoice, request_key))
            )


# Stable callable import for integrations; URLs use the explicit class.
payment_attempts = PaymentAttemptsView.as_view()


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


class PaymentAttemptDetailView(FeatureAPIView):
    name = "Payment Attempt Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "owner_payables",
            "payment_attempt_detail",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, attempt_id):
        return Response(
            payment_attempt_payload(_attempt(request, attempt_id), request.user)
        )


# Stable callable import for integrations; URLs use the explicit class.
payment_attempt_detail = PaymentAttemptDetailView.as_view()


class PaymentAttemptReconcileView(FeatureAPIView):
    name = "Payment Attempt Reconcile"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    throttle_classes = [PaymentReconcileThrottle]
    action_policies = {
        "post": ActionPolicy(
            "owner_payables",
            "payment_attempt_reconcile",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, attempt_id):
        candidate = _attempt(request, attempt_id, allow_original_payer=True)
        if hasattr(candidate, "paymob_payment"):
            if request.user.pk != candidate.payer_id:
                raise PermissionDenied(
                    "Only the original payer can reconcile this attempt."
                )
            if (
                request.data.get("action") or request.data.get("decision")
            ) != "reconcile" or request.data.get(
                "expected_revision"
            ) != candidate.revision:
                raise RentalConflict(
                    "Payment attempt revision or action is invalid.",
                    code="stale_revision",
                )
            from ..services.paymob_payments import reconcile

            return Response(
                payment_attempt_payload(
                    reconcile(candidate.paymob_payment), request.user
                )
            )
        with transaction.atomic():
            attempt = _attempt(
                request, attempt_id, lock=True, allow_original_payer=True
            )
            if request.user != attempt.payer:
                raise PermissionDenied("Only the payer can reconcile this attempt.")
            if (
                request.data.get("action") or request.data.get("decision")
            ) != "reconcile" or int(
                request.data.get("expected_revision", 0)
            ) != attempt.revision:
                raise RentalConflict(
                    "Payment attempt revision or action is invalid.",
                    code="stale_revision",
                )
            return Response(payment_attempt_payload(attempt, request.user))


# Stable callable import for integrations; URLs use the explicit class.
payment_attempt_reconcile = PaymentAttemptReconcileView.as_view()


class OwnerPayablesView(FeatureAPIView):
    name = "Owner Payables"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "owner_payables",
            "owner_payables",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        if request.query_params.get("projection") == "compact_v1":
            from ..financial_http import compact_financial_response

            return compact_financial_response(request, "payables")
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


# Stable callable import for integrations; URLs use the explicit class.
owner_payables = OwnerPayablesView.as_view()


from ..services.payment_events import (
    apply_fake_payment_event as apply_fake_payment_event,
)

__all__ = [
    "OwnerPayablesView",
    "PaymentAttemptDetailView",
    "PaymentAttemptReconcileView",
    "PaymentAttemptsView",
    "_validated_navigation",
    "apply_fake_payment_event",
    "owner_payables",
    "payment_attempt_detail",
    "payment_attempt_reconcile",
    "payment_attempts",
]
