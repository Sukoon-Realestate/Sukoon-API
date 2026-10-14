"""Planning transition views: transition projection."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from ..models import Lease, RentalInterest
from ..planning_models import TenancyTransition
from ..planning_condition_views import participant_lease
from ..services.planning import check_revision


TERMINAL = {"withdrawn", "declined", "cancelled", "expired", "effective"}


def transition_actions(user, item):
    if item.status in TERMINAL or item.lease.legacy_read_only:
        return []
    if item.kind == "moveOutNotice":
        return (
            ["withdraw"]
            if user.pk == item.author_id
            else (["acknowledge"] if item.status == "submitted" else [])
        )
    if user.pk == item.lease.owner_id:
        actions = ["nominate", "decline", "cancel"]
        if not item.availability_approved:
            actions.append("approve_availability")
        if item.candidate_consented and not item.candidate_approved:
            actions.append("approve_candidate")
        return actions
    return ["withdraw"] if user.pk == item.author_id else []


def transition_projection(item):
    released = (
        item.lease.status == "ended" and item.lease.occupancy_status == "returned"
    )
    incoming = None
    if item.candidate_id:
        incoming = (
            Lease.objects.filter(
                property=item.lease.property,
                owner=item.lease.owner,
                tenant=item.candidate.tenant,
                offer_id=item.lease.offer_id,
                tenancy_invitation__interest=item.candidate,
                start_date__gte=item.requested_on,
                legacy_read_only=False,
            )
            .exclude(pk=item.lease_id)
            .exclude(status__in=["cancelled", "expired"])
            .order_by("-created_at")
            .first()
        )
    return {
        "outgoing_release_status": "released" if released else "pending",
        "incoming_agreement_status": incoming.status if incoming else "not_started",
        "future_availability_status": (
            "approved"
            if released and item.availability_approved
            else (
                "awaiting_possession_return"
                if item.availability_approved
                else "pending_approval"
            )
        ),
        "incoming_lease_id": str(incoming.id) if incoming else "",
    }


def transition_payload(item, user):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "kind": item.kind,
        "status": item.status,
        "revision": item.revision,
        "requested_on": str(item.requested_on),
        "received_at": item.created_at.isoformat(),
        "effective_on": str(item.effective_on) if item.effective_on else "",
        "reason": item.reason,
        "candidate_id": str(item.candidate.id) if item.candidate_id else "",
        "candidate_revision": item.candidate_revision,
        "candidate_consented": item.candidate_consented,
        **transition_projection(item),
        "history": item.history,
        "allowed_actions": transition_actions(user, item),
        "blocking_reasons": [],
    }


def transition_for(user, identifier, kind, *, lock=False):
    item = get_object_or_404(TenancyTransition, id=identifier, kind=kind)
    participant_lease(user, item.lease.id, lock=lock)
    return get_object_or_404(
        (
            TenancyTransition.objects.select_for_update()
            if lock
            else TenancyTransition.objects.all()
        ),
        pk=item.pk,
    )


def _candidates(lease):
    return (
        RentalInterest.objects.filter(
            property=lease.property,
            offer_id=lease.offer_id,
            tenant__is_active=True,
            tenant__is_verified=True,
            status__in=["submitted", "under_review", "proposed", "invited"],
        )
        .exclude(tenant_id__in=[lease.owner_id, lease.tenant_id])
        .order_by("-created_at", "pkid")
    )


def _nominate(request, item):
    if request.user.pk != item.lease.owner_id:
        raise PermissionDenied(
            "Only the owner can nominate a candidate from their authorized rental interests."
        )
    candidate = get_object_or_404(
        _candidates(item.lease), id=request.data.get("candidate_id")
    )
    check_revision(candidate.revision, request.data.get("candidate_revision"))
    item.candidate = candidate
    item.candidate_revision = candidate.revision
    item.candidate_consented = False
    item.candidate_approved = False
    item.status = "candidate_pending"
