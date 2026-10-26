"""Private owner updates, committed with the result and resolved by exact identity."""

import uuid
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from core_apps.features.planning_models import PlanningEvent
from .models import TourRevision
from .capture_models import CaptureProcessingJob
from .policy import owner_property

ACTION = "open_tour_update"
EVENT = "tour_owner_update"
LABELS = {
    "ready": ("نتيجة الجولة جاهزة للمراجعة", "Tour result ready for review"),
    "failed": ("تعذرت معالجة الجولة", "Tour processing needs attention"),
    "approved": ("اعتُمد إصدار الجولة", "Tour revision approved"),
    "rejected": ("تحتاج الجولة إلى تصحيح", "Tour revision needs correction"),
    "capture_result": ("تحديث نتيجة التصوير", "Capture result updated"),
    "capture_failed": ("تعذرت معالجة التصوير", "Capture processing needs attention"),
    "capture_cancelled": ("أُلغيت معالجة التصوير", "Capture processing cancelled"),
}


def record(recipient_id, key, change, identity):
    identifier = uuid.uuid4()
    return PlanningEvent.objects.get_or_create(
        recipient_id=recipient_id,
        event_key=key,
        defaults={
            "id": identifier,
            "destination": {
                "schema_version": "1",
                "action_type": ACTION,
                "event_kind": EVENT,
                "target_id": str(identifier),
                "workspace": "owner",
                "change": change,
                **identity,
            },
        },
    )[0]


def record_tour(revision, change, attempt=""):
    tour = revision.tour
    target = tour.target
    recipient = target.owner_id if tour.target_kind == "property" else target.manager_id
    return record(
        recipient,
        f"tour:{revision.id}:{revision.draft_version}:{change}:{attempt}",
        change,
        {
            "source_kind": "tour",
            "asset_kind": tour.target_kind,
            "asset_id": str(target.id),
            "tour_id": str(tour.id),
            "revision_id": str(revision.id),
            "draft_version": revision.draft_version,
        },
    )


def record_capture(job):
    session = job.manifest.session
    change = {"failed": "capture_failed", "cancelled": "capture_cancelled"}.get(
        job.state, "capture_result"
    )
    return record(
        session.owner_id,
        f"capture:{job.id}:{job.attempt}:{change}",
        change,
        {
            "source_kind": "capture",
            "asset_kind": "property",
            "asset_id": str(session.property.id),
            "session_id": str(session.id),
            "job_id": str(job.id),
            "manifest_revision": job.manifest.revision,
            "manifest_hash": job.manifest.sha256,
        },
    )


def resolve(event, *, allow_unavailable=False):
    data = event.destination
    if not isinstance(data, dict) or (
        data.get("action_type") != ACTION
        or data.get("event_kind") != EVENT
        or data.get("workspace") != "owner"
        or data.get("target_id") != str(event.id)
        or data.get("change") not in LABELS
    ):
        raise NotFound()
    asset = owner_property(
        event.recipient, data.get("asset_id"), data.get("asset_kind")
    )
    if data.get("source_kind") == "capture":
        job = get_object_or_404(
            CaptureProcessingJob.objects.select_related("manifest__session"),
            id=data.get("job_id"),
            manifest__session__id=data.get("session_id"),
            manifest__session__owner=event.recipient,
            manifest__session__property=asset,
            manifest__revision=data.get("manifest_revision"),
            manifest__sha256=data.get("manifest_hash"),
        )
        available = job.manifest.session.deleted_at is None
        item = job
    elif data.get("source_kind") == "tour":
        item = get_object_or_404(
            TourRevision.objects.select_related("tour"),
            id=data.get("revision_id"),
            tour__id=data.get("tour_id"),
            **{f"tour__{data['asset_kind']}": asset},
        )
        available = not item.tour.deleted
    else:
        raise NotFound()
    if not available and not allow_unavailable:
        raise NotFound()
    return item, available


def notification_copy(event):
    resolve(event)
    ar, en = LABELS[event.destination["change"]]
    return {
        "title": f"{ar} / {en}",
        "body": "راجع النتيجة الحالية وسجل التغيير قبل المتابعة. / Review the current result and history before continuing.",
    }


def update_payload(event):
    item, available = resolve(event, allow_unavailable=True)
    data = event.destination
    history = PlanningEvent.objects.filter(
        recipient=event.recipient,
        destination__action_type=ACTION,
        **(
            {"destination__job_id": data["job_id"]}
            if data["source_kind"] == "capture"
            else {"destination__tour_id": data["tour_id"]}
        ),
    ).order_by("-created_at")[:100]
    result = {
        "id": str(event.id),
        "source_kind": data["source_kind"],
        "asset_id": data["asset_id"],
        "asset_kind": data["asset_kind"],
        "available": available,
        "workspace": "owner",
        "history": [
            {
                "id": str(e.id),
                "change": e.destination["change"],
                "created_at": e.created_at.isoformat(),
                "revision": e.destination.get(
                    "draft_version", e.destination.get("manifest_revision")
                ),
            }
            for e in history
        ],
    }
    if data["source_kind"] == "capture":
        from .capture_services import job_payload

        result.update(session_id=data["session_id"], job=job_payload(item))
    else:
        from .services import revision_payload, tour_payload

        result.update(tour=tour_payload(item.tour), revision=revision_payload(item))
    return result
