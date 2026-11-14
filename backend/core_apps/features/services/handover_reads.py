"""Handover access, evidence and prepared response metadata."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError
from ..models import Lease, RentalEvidence, RentalHandover
from ..providers import require_verified_rental_account
from .lease_permissions import handover_actions
from .evidence_projection import evidence_payload


def _money(value):
    return {"amount_minor": value, "currency": "EGP", "exponent": 2}


def handover_payload(item, user=None):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "kind": item.kind,
        "status": item.status,
        "possession_on": str(item.possession_on),
        "condition": item.condition,
        "keys": item.keys,
        "meters": item.meters,
        "inventory": item.inventory,
        "evidence": [evidence_payload(x) for x in item.evidence.all()],
        "accepted_by": item.approvals,
        "allowed_actions": handover_actions(user, item),
        "blocking_reasons": [],
    }


def _validate_evidence(lease, ids):
    if len(ids) > 5:
        raise ValidationError({"evidence_ids": "At most five images are supported."})
    evidence = list(
        RentalEvidence.objects.filter(
            id__in=ids,
            lease=lease,
            malware_status=RentalEvidence.MalwareStatus.SAFE,
            deleted_at__isnull=True,
        )
    )
    if len(evidence) != len(set(map(str, ids))):
        raise ValidationError(
            {"evidence_ids": "Every item must be safe evidence for this lease."}
        )
    return evidence


def current_actor(actor, claims, *, lock=False, write=False):
    if not write:
        return actor
    from core_apps.users.models import User
    from core_apps.users.services.sessions import validate_session

    users = User.objects.select_for_update() if lock else User.objects
    actor = users.get(pk=actor.pk)
    validate_session(actor, claims or {})
    require_verified_rental_account(actor)
    return actor


def lease_for(actor, claims, lease_id, *, lock=False, write=False):
    actor = current_actor(actor, claims, lock=lock, write=write)
    queryset = Lease.objects.select_related("owner", "tenant")
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    lease = get_object_or_404(queryset, id=lease_id)
    from .rental_lifecycle.locks import require_personal_workflow

    require_personal_workflow(lease)
    if actor not in (lease.owner, lease.tenant):
        raise NotFound()
    return actor, lease


def handover_for(actor, claims, handover_id, *, lock=False, write=False):
    actor = current_actor(actor, claims, lock=lock, write=write)
    if lock:
        reference = get_object_or_404(RentalHandover, id=handover_id)
        Lease.objects.select_for_update().get(pk=reference.lease_id)
    queryset = RentalHandover.objects.select_related(
        "lease__owner", "lease__tenant"
    ).prefetch_related("evidence")
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    item = get_object_or_404(queryset, id=handover_id)
    from .rental_lifecycle.locks import require_personal_workflow

    require_personal_workflow(item.lease)
    if actor not in (item.lease.owner, item.lease.tenant):
        raise NotFound()
    return actor, item
