"""Rental phase3 views: rent invoice quote."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from ..models import IdempotencyRecord
from ..renderers import FeatureJsonRenderer
from ..services.rental_lifecycle.locks import lock_financial_lease as _lock_lease


class PaymentReconcileThrottle(UserRateThrottle):
    # Inquiry has its own allowance; catalog/invoice GETs use the general user
    # bucket and must not exhaust the first payment verification request.
    scope = "payment_reconcile"
    rate = "6/min"


from core_apps.features.services.money_projection import _money as _money


def _invoice(request, invoice_id, lock=False):
    from ..services.money_access import rental_invoice_for

    return rental_invoice_for(request.user, invoice_id, lock)


def _attempt(request, attempt_id, lock=False, allow_original_payer=False):
    from ..services.money_access import payment_attempt_for

    return payment_attempt_for(request.user, attempt_id, lock, allow_original_payer)


def _active_session(attempt):
    session = getattr(attempt, "checkout_session", None)
    if (
        not session
        or not session.hosted_url
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
    if hasattr(attempt, "paymob_payment"):
        from ..services.paymob_payments import session_payload

        resource = session_payload(attempt)
    else:
        resource = receipt.response_data.get("resource", {})
    if resource.get("session_id") != str(session.id) or resource.get(
        "payment_attempt_id"
    ) != str(attempt.id):
        return None
    return {**resource, "operation_receipt_id": str(receipt.id)}


from core_apps.features.services.money_projection import quote_payload as quote_payload


class RentInvoiceQuoteView(FeatureAPIView):
    name = "Rent Invoice Quote"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "rent_invoice_quote",
            "rent_invoice_quote",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, invoice_id):
        from ..services.rental_payment_commands import quote_rent

        result = quote_rent(
            request.user,
            request.auth,
            request.data,
            request.headers.get("X-Sokoun-Authorization", ""),
            invoice_id,
        )
        return Response(result.data, status=result.status)


# Stable callable import for integrations; URLs use the explicit class.
rent_invoice_quote = RentInvoiceQuoteView.as_view()

__all__ = [
    "_lock_lease",
    "PaymentReconcileThrottle",
    "RentInvoiceQuoteView",
    "_active_session",
    "_attempt",
    "_invoice",
    "_money",
    "can_pay",
    "quote_payload",
    "rent_invoice_quote",
]

from ..services.company.tenancy_access import can_pay
