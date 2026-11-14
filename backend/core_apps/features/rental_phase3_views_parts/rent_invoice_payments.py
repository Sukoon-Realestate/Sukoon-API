"""Discover original payment history through its currently authorized invoice."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from rest_framework.permissions import IsAuthenticated
from ..models import PaymentAttempt
from ..pagination import FeaturePagination
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase3 import payment_attempt_payload
from .rent_invoice_quote import _invoice


class RentInvoicePaymentsView(FeatureAPIView):
    name = "Rent Invoice Payments"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "rent_invoice_payments",
            "rent_invoice_payments",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, invoice_id):
        invoice = _invoice(request, invoice_id)
        attempts = (
            PaymentAttempt.objects.filter(invoice=invoice)
            .select_related("invoice__lease", "quote", "receipt", "chargeback")
            .order_by("-created_at", "-id")
        )
        paginator = FeaturePagination()
        page = paginator.paginate_queryset(attempts, request)
        response = paginator.get_paginated_response(
            [payment_attempt_payload(attempt, request.user) for attempt in page]
        )
        response["Cache-Control"] = "private, no-store"
        return response


# Stable callable import for integrations; URLs use the explicit class.
rent_invoice_payments = RentInvoicePaymentsView.as_view()

__all__ = ["RentInvoicePaymentsView", "rent_invoice_payments"]
