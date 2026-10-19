"""Rental phase5 views: maintenance payload."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from ..models import Lease, MaintenanceRequest, RentalEvidence, PrivateAccessRevocation
from ..providers import require_rental_provider
from ..services.cycle_permissions import cycle_actions


MAINTENANCE_ACTIONS = {
    "acknowledge",
    "reply",
    "propose_appointment",
    "accept_appointment",
    "start_work",
    "report_missed",
    "report_resolved",
    "confirm_resolved",
    "reopen",
    "cancel",
    "propose_cost",
    "approve_cost",
    "reject_cost",
}


def _money(value):
    return (
        None
        if value is None
        else {"amount_minor": value, "currency": "EGP", "exponent": 2}
    )


def _assert_private_access(lease, user):
    if (
        not user.is_active
        or PrivateAccessRevocation.objects.filter(lease=lease, user=user).exists()
    ):
        raise NotFound()


def _lease(request, lease_id, lock=False, servicing=False):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if servicing:
            from ..services.rental_lifecycle.common import require_actor

            require_actor(request.user)
        else:
            require_rental_provider(request.user)
    queryset = Lease.objects.select_related("owner", "tenant")
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    lease = get_object_or_404(queryset, id=lease_id)
    from ..services.rental_lifecycle.locks import require_personal_workflow

    require_personal_workflow(lease)
    if request.user not in (lease.owner, lease.tenant):
        raise NotFound()
    _assert_private_access(lease, request.user)
    if lease.legacy_read_only:
        raise PermissionDenied("Legacy rentals are read-only.")
    return lease


def _safe_evidence(lease, ids):
    items = list(
        RentalEvidence.objects.filter(
            id__in=ids, lease=lease, malware_status=RentalEvidence.MalwareStatus.SAFE
        )
    )
    if len(items) != len(set(map(str, ids))):
        raise ValidationError(
            {"evidence_ids": "Evidence must be safe and belong to this lease."}
        )
    return items


def maintenance_payload(item, user=None):
    return {
        "allowed_actions": cycle_actions(user, item),
        "blocking_reasons": [],
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "title": item.title,
        "description": item.description,
        "category": item.category,
        "priority": item.priority,
        "access_times": item.access_times,
        "status": item.status,
        "appointment_at": (
            item.appointment_at.isoformat() if item.appointment_at else None
        ),
        "appointment_version": item.appointment_version,
        "appointment_ends_at": (
            item.appointment_ends_at.isoformat() if item.appointment_ends_at else None
        ),
        "access_approved_version": item.access_approved_version,
        "proposed_cost": _money(item.proposed_cost_minor),
        "cost_payer": item.cost_payer or None,
        "cost_version": item.cost_version,
        "approved_cost_version": item.approved_cost_version,
        "events": [
            {
                "id": str(x.id),
                "label": x.action,
                "note": x.note,
                "at": x.created_at.isoformat(),
                "appointment_at": (
                    x.appointment_at.isoformat() if x.appointment_at else None
                ),
                "cost": _money(x.cost_minor),
            }
            for x in item.events.all()
        ],
        "evidence": [
            {"id": str(x.id), "sha256": x.sha256, "status": "ready"}
            for x in item.evidence.all()
        ],
    }


def _maintenance(request, request_id, lock=False):
    queryset = MaintenanceRequest.objects.select_related(
        "lease__owner", "lease__tenant"
    ).prefetch_related("events", "evidence")
    item = get_object_or_404(queryset, id=request_id)
    from ..services.rental_lifecycle.locks import require_personal_workflow

    require_personal_workflow(item.lease)
    if lock:
        lease = Lease.objects.select_for_update().get(pk=item.lease_id)
        item = queryset.select_for_update(of=("self",)).get(pk=item.pk)
        item.lease = lease
    if request.user not in (item.lease.owner, item.lease.tenant):
        raise NotFound()
    _assert_private_access(item.lease, request.user)
    return item
