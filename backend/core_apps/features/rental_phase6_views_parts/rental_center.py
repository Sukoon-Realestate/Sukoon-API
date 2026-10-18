"""Rental phase6 views: rental center."""

from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import RentInvoice
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase6 import closure_blocking_reasons
from .final_settlement_propose import _money, _lease
from ..services.cycle_permissions import cycle_actions
from ..services.rental_notes import response_note_label


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
    next_action = None
    if not lease.legacy_read_only:
        if lease.status in {"draft", "pending_signatures", "pending"}:
            next_action = {
                "action": "review_agreement",
                "resource_id": str(lease.id),
                "description": "Review the current agreement and signature status.",
                "kind": "lease_review",
            }
        else:
            invoice = (
                lease.invoices.filter(status__in=["due", "overdue", "partially_paid"])
                .order_by("due_date", "pk")
                .first()
            )
            handover = (
                lease.handovers.exclude(status="accepted")
                .order_by("-created_at")
                .first()
            )
            if invoice:
                next_action = {
                    "action": "review_invoice",
                    "resource_id": str(invoice.id),
                    "description": "Review the outstanding invoice and any original payment attempt.",
                    "kind": "invoice",
                }
            elif handover:
                next_action = {
                    "action": "review_handover",
                    "resource_id": str(handover.id),
                    "description": "Review possession, condition and the remaining participant approvals.",
                    "kind": "handover",
                }
            elif (
                lease.status in {"ended", "cancelled"}
                and lease.financial_closure_status != "closed"
            ):
                next_action = {
                    "action": "resolve_closure",
                    "resource_id": str(lease.id),
                    "description": (
                        reasons[0]
                        if reasons
                        else "Review final settlement and remaining closure requirements."
                    ),
                    "kind": "closure",
                }
    from core_apps.chat.models import Conversation

    chat = (
        Conversation.objects.filter(kind="direct", participant_set__user=lease.owner)
        .filter(participant_set__user=lease.tenant)
        .order_by("created_at", "pk")
        .first()
    )
    timeline = [
        {
            "id": str(item.id),
            "label": response_note_label(
                item, request.headers.get("Accept-Language", "en")
            ),
            "description": item.description,
            "occurred_at": item.occurred_at.isoformat(),
            "kind": item.kind,
            "resource_id": str(item.resource_id) if item.resource_id else None,
        }
        for item in lease.timeline_events.all()[:20]
    ]
    schedule = [
        {
            "id": str(period.id),
            "sequence": period.sequence,
            "start": str(period.start),
            "end_exclusive": str(period.end_exclusive),
            "issue_at": period.issue_at.isoformat(),
            "due_at": period.due_at.isoformat(),
            "amount": _money(period.amount_minor),
            "status": period.status,
            "invoice_id": (
                str(period.invoice.id) if hasattr(period, "invoice") else None
            ),
        }
        for period in lease.billing_periods.select_related("invoice").order_by(
            "sequence"
        )[:12]
    ]
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
            "timeline": timeline,
            "billing_schedule": schedule,
            "timeline_has_more": lease.timeline_events.count() > len(timeline),
            "billing_schedule_has_more": lease.billing_periods.count() > len(schedule),
            "chat_thread_id": str(chat.id) if chat else None,
            "allowed_actions": cycle_actions(request.user, lease),
            "blocking_reasons": reasons,
            "last_updated_at": lease.updated_at.isoformat(),
            "legacy_read_only": lease.legacy_read_only,
            "offer_snapshot": lease.offer_snapshot,
            "closure_blocking_reasons": reasons,
        }
    )
