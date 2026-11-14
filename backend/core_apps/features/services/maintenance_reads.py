"""Personal maintenance access and read projections; no HTTP request dependency."""

from django.shortcuts import get_object_or_404

from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from core_apps.common.translation import translate_message

from ..models import Lease, MaintenanceRequest, RentalEvidence, PrivateAccessRevocation

from ..providers import require_verified_rental_account

from .cycle_permissions import cycle_actions

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

MAINTENANCE_EVENT_LABELS = {
    "created": "Maintenance request submitted.",
    "acknowledge": "Maintenance request acknowledged.",
    "reply": "Maintenance reply added.",
    "propose_appointment": "Maintenance appointment proposed.",
    "accept_appointment": "Maintenance appointment accepted.",
    "start_work": "Maintenance work started.",
    "report_missed": "Missed maintenance appointment reported.",
    "report_resolved": "Maintenance resolution reported.",
    "confirm_resolved": "Maintenance resolution confirmed.",
    "reopen": "Maintenance request reopened.",
    "cancel": "Maintenance request cancelled.",
    "propose_cost": "Maintenance cost proposed.",
    "approve_cost": "Maintenance cost approved.",
    "reject_cost": "Maintenance cost rejected.",
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


def _safe_evidence(lease, ids):
    items = list(
        RentalEvidence.objects.filter(
            id__in=ids,
            lease=lease,
            malware_status=RentalEvidence.MalwareStatus.SAFE,
            deleted_at__isnull=True,
        )
    )
    if len(items) != len(set(map(str, ids))):
        raise ValidationError(
            {"evidence_ids": "Evidence must be safe and belong to this lease."}
        )
    return items


def maintenance_payload(item, user=None, *, invoice_links=None):
    from .billing_sources import source_invoices
    from .evidence_projection import evidence_payload

    return {
        "billing_invoices": (
            source_invoices("maintenance", item.id)
            if invoice_links is None
            else invoice_links
        ),
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
                "action": x.action,
                "label": translate_message(
                    MAINTENANCE_EVENT_LABELS.get(x.action, x.action)
                ),
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
            evidence_payload(x) for x in item.evidence.all() if not x.deleted_at
        ],
    }


def lease_for(actor, lease_id, *, lock=False, servicing=False, write=False):
    if write:
        if servicing:
            from .rental_lifecycle.common import require_actor

            require_actor(actor)
        else:
            require_verified_rental_account(actor)
    queryset = Lease.objects.select_related("owner", "tenant")
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    lease = get_object_or_404(queryset, id=lease_id)
    from .rental_lifecycle.locks import require_personal_workflow

    require_personal_workflow(lease)
    if actor not in (lease.owner, lease.tenant):
        raise NotFound()
    _assert_private_access(lease, actor)
    if lease.legacy_read_only:
        raise PermissionDenied("Legacy rentals are read-only.")
    return lease


def maintenance_for(actor, request_id, *, lock=False):
    queryset = MaintenanceRequest.objects.select_related(
        "lease__owner", "lease__tenant"
    ).prefetch_related("events", "evidence")
    item = get_object_or_404(queryset, id=request_id)
    from .rental_lifecycle.locks import require_personal_workflow

    require_personal_workflow(item.lease)
    if lock:
        lease = Lease.objects.select_for_update().get(pk=item.lease_id)
        item = queryset.select_for_update(of=("self",)).get(pk=item.pk)
        item.lease = lease
    if actor not in (item.lease.owner, item.lease.tenant):
        raise NotFound()
    _assert_private_access(item.lease, actor)
    return item


def collection_payload(lease, actor):
    """Prepare invoice links once for the compatible complete collection."""
    from .billing_sources import source_invoice_map

    items = list(lease.maintenance_requests.prefetch_related("events", "evidence"))
    links = source_invoice_map("maintenance", [item.id for item in items])
    results = [
        maintenance_payload(item, actor, invoice_links=links.get(str(item.id), []))
        for item in items
    ]
    return {"count": len(results), "next": None, "previous": None, "results": results}
