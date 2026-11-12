"""Request-local capture projections; limits apply per session and per job in SQL."""

from collections import defaultdict

from django.db.models import F, OuterRef, Prefetch, Subquery, Window
from django.db.models.functions import RowNumber

from .capture_models import CaptureManifestRevision, CaptureProcessingJob, CaptureRoom
from .models import TourRevision, TourReviewEvent


def prepare_sessions(rows):
    rows = list(rows)
    if not rows:
        return rows
    identities = [row.pk for row in rows]
    latest = (
        CaptureManifestRevision.objects.filter(session_id__in=identities)
        .annotate(
            position=Window(
                RowNumber(), partition_by=[F("session_id")], order_by=[F("revision").desc(), F("pk").desc()]
            )
        )
        .filter(position=1)
    )
    manifests = {row.session_id: row for row in latest}
    revisions = (
        TourRevision.objects.select_related("tour", "capture_job")
        .annotate(
            prepared_review_reason=Subquery(
                TourReviewEvent.objects.filter(
                    revision_id=OuterRef("pk"), decision="rejected", source_hash=OuterRef("source_hash")
                )
                .order_by("-created_at", "-pk")
                .values("public_reason")[:1]
            )
        )
        .prefetch_related("assets", "variants")
        .order_by("-created_at", "-pk")
    )
    jobs = (
        CaptureProcessingJob.objects.filter(manifest__session_id__in=identities)
        .select_related("manifest", "retry_job")
        .annotate(
            position=Window(
                RowNumber(),
                partition_by=[F("manifest__session_id")],
                order_by=[F("manifest__revision").desc(), F("created_at").desc(), F("pk").desc()],
            )
        )
        .filter(position__lte=20)
        .prefetch_related(Prefetch("tour_revisions", queryset=revisions[:2], to_attr="prepared_revisions"))
    )
    sessions = {row.pk: row for row in rows}
    grouped = defaultdict(list)
    for job in jobs.order_by("-manifest__revision", "-created_at", "-pk"):
        job.manifest.session = sessions[job.manifest.session_id]
        grouped[job.manifest.session_id].append(job)
    rooms = defaultdict(list)
    for room in CaptureRoom.objects.filter(session_id__in=identities):
        rooms[room.session_id].append(room)
    for row in rows:
        row.prepared_manifest = manifests.get(row.pk)
        row.prepared_jobs = grouped[row.pk]
        row.prepared_rooms = rooms[row.pk]
    return rows


def job_summary(job):
    return {
        "id": str(job.id),
        "manifestRevision": job.manifest.revision,
        "state": job.state,
        "stage": job.stage,
        "attempt": job.attempt,
        "cancelRequested": job.cancel_requested,
        "detailPath": f"property-captures/{job.manifest.session.id}/processing-jobs/{job.id}/",
    }


def summary_rows(rows):
    """Counts/latest metadata only; do not fetch job outputs or manifest documents."""
    from django.db.models import Count

    jobs = (
        CaptureProcessingJob.objects.filter(manifest__session_id=OuterRef("pk"))
        .order_by()
        .values("manifest__session_id")
        .annotate(total=Count("pk"))
        .values("total")
    )
    rooms = (
        CaptureRoom.objects.filter(session_id=OuterRef("pk"))
        .order_by()
        .values("session_id")
        .annotate(total=Count("pk"))
        .values("total")
    )
    return rows.annotate(prepared_job_count=Subquery(jobs), prepared_room_count=Subquery(rooms))


def session_summary(session):
    return {
        "id": str(session.id),
        "propertyId": str(session.property.id),
        "clientSessionId": str(session.client_id),
        "state": session.state,
        "revision": session.revision,
        "policyVersion": session.policy_version,
        "coachOptIn": session.coach_opt_in,
        "roomCount": session.prepared_room_count or 0,
        "jobCount": session.prepared_job_count or 0,
        "detailPath": f"property-captures/{session.id}/",
        "jobsPath": f"property-captures/{session.id}/processing-jobs/",
    }
