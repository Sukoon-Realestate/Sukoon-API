"""Discover original payment history through its currently authorized invoice."""

from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from ..models import PaymentAttempt
from ..pagination import FeaturePagination
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase3 import payment_attempt_payload
from .rent_invoice_quote import _invoice


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rent_invoice_payments(request, invoice_id):
    # Reading retained obligations is independent of checkout/provider readiness.
    # Use the same current commercial/beneficiary access as payment detail, never
    # a caller-supplied company, payer or recovery request key.
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
