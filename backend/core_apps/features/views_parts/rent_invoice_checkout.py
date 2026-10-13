"""Views: rent invoice checkout."""

from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import CheckoutSession, RentInvoice
from ..renderers import FeatureJsonRenderer
from .rental_operation_lookup import _replay, _remember
from .lease_cancel import _get_authorized_invoice


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rent_invoice_checkout(request, invoice_id):
    invoice = _get_authorized_invoice(request, invoice_id)
    if request.user != invoice.lease.tenant:
        raise PermissionDenied("Only the tenant can pay this invoice.")
    if not getattr(settings, "RENTAL_CHECKOUT_ENABLED", False):
        return Response(
            {
                "message": "Secure rent checkout is not available yet.",
                "code": "capability_unavailable",
                "subject_id": str(invoice.id),
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    if str(request.data.get("invoice_id")) != str(invoice.id) or not request.data.get(
        "request_key"
    ):
        raise ValidationError(
            {
                "invoice_id": "The body invoice_id must match the path and request_key is required."
            }
        )
    if invoice.status not in {RentInvoice.Status.DUE, RentInvoice.Status.OVERDUE}:
        raise ValidationError("This invoice is not payable.")
    replay = _replay(
        request.user, "invoice.checkout", request.data["request_key"], request.data
    )
    if replay:
        return replay
    expires = timezone.now() + timedelta(minutes=15)
    base = getattr(settings, "FEATURE_HOSTED_BASE_URL", "https://sokoun.app")
    with transaction.atomic():
        session = CheckoutSession.objects.create(
            invoice=invoice,
            payer=request.user,
            hosted_url=f"{base.rstrip('/')}/payments/{invoice.id}",
            expires_at=expires,
        )
        data = {
            "id": str(session.id),
            "subject_id": str(invoice.id),
            "status": "pending",
            "hosted_url": session.hosted_url,
            "expires_at": expires.isoformat(),
            "amount": {
                "amount_minor": invoice.amount_minor,
                "currency": invoice.currency,
                "exponent": invoice.exponent,
            },
            "message": "",
        }
        _remember(
            request.user,
            "invoice.checkout",
            request.data["request_key"],
            request.data,
            data,
            201,
            request_subject_id=invoice.id,
            result_subject_id=invoice.id,
            result_revision=invoice.revision,
            is_rental_operation=True,
        )
    return Response(data, status=status.HTTP_201_CREATED)
