"""Rental phase6 views: rental center."""

from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import RentInvoice
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase6 import closure_blocking_reasons
from .final_settlement_propose import _money, _lease


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_center(request, lease_id):
    lease = _lease(request, lease_id)
    reasons = closure_blocking_reasons(lease)
    balance = sum(
        max(x.charges_minor - x.credits_minor - x.applied_minor, 0)
        for x in lease.invoices.exclude(
            status__in=[RentInvoice.Status.CANCELLED, RentInvoice.Status.WRITTEN_OFF]
        )
    )
    next_action = (
        {
            "action": "resolve_closure",
            "resource_id": str(lease.id),
            "description": reasons[0],
            "kind": "closure",
        }
        if reasons
        else None
    )
    return Response(
        {
            "id": str(lease.id),
            "tenancy_root_id": str(lease.tenancy_root_id),
            "revision": lease.revision,
            "property_title": lease.property.title,
            "lease_status": lease.status,
            "status": lease.status,
            "occupancy_status": lease.occupancy_status,
            "financial_closure_status": lease.financial_closure_status,
            "terms": lease.terms,
            "balance": _money(balance),
            "next_action": next_action,
            "timeline": [],
            "billing_schedule": [],
            "chat_thread_id": None,
            "last_updated_at": lease.updated_at.isoformat(),
            "legacy_read_only": lease.legacy_read_only,
            "offer_snapshot": lease.offer_snapshot,
            "closure_blocking_reasons": reasons,
        }
    )
