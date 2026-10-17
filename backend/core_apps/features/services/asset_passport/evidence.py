from django.http import Http404
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError, NotFound
from ...models import RentalHandover, MaintenanceRequest
from ...planning_models import ConditionReport
from ..planning import check_revision
from .access import leases_for, lease_covers

SOURCES = {
    "condition_report": ConditionReport,
    "handover": RentalHandover,
    "maintenance": MaintenanceRequest,
}


def source_for(user, kind, identifier):
    model = SOURCES.get(kind)
    if model is None:
        raise ValidationError(
            {
                "source_kind": "Select an existing condition report, handover, or maintenance request."
            }
        )
    source = get_object_or_404(
        model.objects.select_related("lease__property"),
        id=identifier,
        lease__in=leases_for(user),
    )
    # An unsubmitted report is its author's working document.
    if (
        kind == "condition_report"
        and source.status == "draft"
        and source.author_id != user.pk
    ):
        raise NotFound()
    return source


def safe_evidence(source):
    return source.evidence.filter(
        lease=source.lease, purpose="rental", deleted_at=None, malware_status="safe"
    )


def source_payload(source, kind, user=None):
    observed = (
        getattr(source, "inspected_on", None)
        or getattr(source, "possession_on", None)
        or timezone.localtime(source.created_at).date()
    )
    return {
        "id": str(source.id),
        "kind": kind,
        "workspace": "owner" if user and source.lease.owner_id == user.pk else "tenant",
        "lease_id": str(source.lease.id),
        "revision": source.revision,
        "status": source.status,
        "observed_on": str(observed),
        "title": getattr(source, "title", ""),
        "evidence": [
            {
                "id": str(row.id),
                "name": row.original_name,
                "sha256": row.sha256,
                "server_received_at": row.created_at.isoformat(),
                "capture_time_status": "not_verified",
            }
            for row in safe_evidence(source)
        ],
    }


def validate(user, asset, data, observed_on):
    source = source_for(user, data.get("source_kind"), data.get("source_id"))
    check_revision(source.revision, data.get("source_revision"))
    location = (
        asset.locations.filter(
            property_id=source.lease.property_id, starts_on__lte=observed_on
        )
        .filter(
            Q(ends_on_exclusive__isnull=True) | Q(ends_on_exclusive__gt=observed_on)
        )
        .first()
    )
    if (
        not location
        or not lease_covers(location, source.lease)
        or not source.lease.start_date <= observed_on < source.lease.end_date
    ):
        raise ValidationError(
            {
                "source_id": "The source tenancy and reported observation date must match the item's location period."
            }
        )
    ids = data.get("evidence_ids", [])
    if (
        not isinstance(ids, list)
        or len(ids) > 20
        or any(not isinstance(value, str) for value in ids)
        or len(set(ids)) != len(ids)
    ):
        raise ValidationError(
            {"evidence_ids": "Choose distinct evidence linked to this source."}
        )
    selected = list(safe_evidence(source).filter(id__in=ids))
    if len(selected) != len(ids):
        raise ValidationError(
            {
                "evidence_ids": "Evidence must belong to this source and have a completed safe scan."
            }
        )
    return source, selected


def visible_observation(row, user):
    try:
        source_for(user, row.source_kind, row.source_id)
        return True
    except (NotFound, Http404):
        return False


def observation_payload(row, user):
    source = source_for(user, row.source_kind, row.source_id)
    safe = set(safe_evidence(source).values_list("id", flat=True))
    return {
        "id": str(row.id),
        "condition": row.condition,
        "capture_context": row.capture_context,
        "note": row.note,
        "observed_on": str(row.observed_on),
        "server_received_at": row.created_at.isoformat(),
        "capture_time_status": "author_reported_not_verified",
        "source_kind": row.source_kind,
        "source_id": str(row.source_id),
        "source_revision": row.source_revision,
        "source_status": row.source_status,
        "current_source_status": source.status,
        "source_changed": source.revision != row.source_revision,
        "lease_id": str(row.lease.id),
        "source_workspace": "owner" if row.lease.owner_id == user.pk else "tenant",
        "evidence_ids": [
            str(pk) for pk in row.evidence.values_list("id", flat=True) if pk in safe
        ],
        "authorship": "self" if row.author_id == user.pk else "tenancy_participant",
        "liability_determined": False,
    }
