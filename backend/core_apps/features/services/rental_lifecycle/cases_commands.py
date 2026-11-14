"""Named cases commands; adapters supply typed data and current actor."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError
from core_apps.properties.models import Property
from core_apps.features.models import Lease, RentalEvidence
from core_apps.features.services.rental_lifecycle.cases import (
    case_payload,
    open_system_case,
)
from core_apps.features.services.rental_lifecycle.common import require_revision
from core_apps.features.services.rental_phase2 import RentalConflict


def rental_cases_post_authorize(*, actor, data):
    lease = get_object_or_404(Lease, id=data["lease_id"])
    if actor.pk not in {lease.owner_id, lease.tenant_id}:
        raise NotFound()
    Property.objects.select_for_update().get(pk=lease.property_id)
    return Lease.objects.select_for_update().get(pk=lease.pk)


def rental_cases_post_execute(lease, *, actor, data):
    require_revision(lease, data["expected_revision"])
    if lease.legacy_read_only:
        raise RentalConflict("Historical agreements require operational review.")
    evidence = list(
        RentalEvidence.objects.filter(
            id__in=data["evidence_ids"],
            lease=lease,
            uploader=actor,
            malware_status="safe",
            deleted_at__isnull=True,
        )
    )
    if len(evidence) != len(set(data["evidence_ids"])):
        raise ValidationError(
            {"evidence_ids": "Use your clean evidence from this agreement."}
        )
    item = open_system_case(
        kind=data["kind"],
        source_key=f"participant-case:{actor.id}:{data['request_key']}",
        lease=lease,
        actor=actor,
        evidence=evidence,
        reason=data["reason"],
        next_action="Review the agreed selection and both participant accounts.",
    )
    if data["kind"] == "habitability":
        from core_apps.features.services.rental_lifecycle.habitability import report

        report(item, data)
    return (item, case_payload(item, actor), 201)
