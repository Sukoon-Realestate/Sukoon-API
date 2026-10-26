"""Rental phase4 views: handover payload."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError
from ..models import Lease, RentalEvidence, RentalHandover
from ..providers import require_verified_rental_account
from ..services.lease_permissions import handover_actions


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


MAX_EVIDENCE_BYTES = 5 * 1024 * 1024


def _current_actor(request, lock=False):
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    from core_apps.users.models import User
    from core_apps.users.services.sessions import validate_session

    users = User.objects.select_for_update() if lock else User.objects
    request.user = users.get(pk=request.user.pk)
    validate_session(request.user, request.auth or {})
    require_verified_rental_account(request.user)


def _money(value):
    return {"amount_minor": value, "currency": "EGP", "exponent": 2}


def _lease(request, lease_id, lock=False):
    _current_actor(request, lock)
    queryset = Lease.objects.select_related("owner", "tenant")
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    lease = get_object_or_404(queryset, id=lease_id)
    from ..services.rental_lifecycle.locks import require_personal_workflow

    require_personal_workflow(lease)
    if request.user not in (lease.owner, lease.tenant):
        raise NotFound()
    return lease


def evidence_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "name": item.original_name,
        "mime_type": item.content_type,
        "size_bytes": item.size_bytes,
        "media_metadata": item.media_metadata or {},
        "status": (
            "ready"
            if item.malware_status == RentalEvidence.MalwareStatus.SAFE
            else item.malware_status
        ),
        "sha256": item.sha256,
        "revision": item.revision,
    }


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


def _handover(request, handover_id, lock=False):
    _current_actor(request, lock)
    if lock:
        reference = get_object_or_404(RentalHandover, id=handover_id)
        Lease.objects.select_for_update().get(pk=reference.lease_id)
    queryset = RentalHandover.objects.select_related(
        "lease__owner", "lease__tenant"
    ).prefetch_related("evidence")
    if lock:
        queryset = queryset.select_for_update(of=("self",))
    handover = get_object_or_404(queryset, id=handover_id)
    from ..services.rental_lifecycle.locks import require_personal_workflow

    require_personal_workflow(handover.lease)
    if request.user not in (handover.lease.owner, handover.lease.tenant):
        raise NotFound()
    return handover


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
