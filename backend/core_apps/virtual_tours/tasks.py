import logging
import shutil
from datetime import timedelta
from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import (
    TourAsset,
    TourOperation,
    TourRevision,
    TourUploadSession,
    TourVariant,
    TourViewerSession,
)
from .processing import process_revision
from .storage import root, path
from . import remote_storage

logger = logging.getLogger(__name__)


def dispatch_revision(revision_id, source_hash):
    if settings.VIRTUAL_TOUR_PROCESSOR_MODE in {"polling", "inline"}:
        # The dedicated tour worker consumes the existing durable DB outbox.
        return
    try:
        process_tour.delay(revision_id, source_hash)
    except Exception:
        # Durable queued state is the outbox; beat retries dispatch after broker recovery.
        logger.warning("tour_dispatch_pending revision=%s", revision_id)


@shared_task(time_limit=900, soft_time_limit=840, acks_late=True)
def process_tour(revision_id, source_hash):
    process_revision(revision_id, source_hash)


def recover_interrupted_tours():
    # Reclaim an interrupted worker, with a bounded number of attempts.
    stale = TourRevision.objects.filter(
        processing_state="processing",
        updated_at__lt=timezone.now() - timedelta(minutes=20),
    )
    for revision in stale:
        attempts = revision.report.get("worker_recoveries", 0) + 1
        TourRevision.objects.filter(
            pk=revision.pk,
            processing_state="processing",
            updated_at=revision.updated_at,
        ).update(
            processing_state="queued" if attempts <= 3 else "failed",
            report={"worker_recoveries": attempts, "code": "worker_interrupted"},
        )


@shared_task
def dispatch_pending_tours():
    recover_interrupted_tours()
    for identity, source_hash in TourRevision.objects.filter(
        processing_state="queued"
    ).values_list("id", "source_hash")[:50]:
        dispatch_revision(str(identity), source_hash)


@shared_task
def cleanup_tours():
    now = timezone.now()
    TourViewerSession.objects.filter(expires_at__lt=now - timedelta(days=1)).delete()
    TourOperation.objects.filter(expires_at__lt=now).exclude(status="expired").update(
        result={}, status="expired"
    )
    TourUploadSession.objects.filter(expires_at__lt=now, state="open").update(
        state="expired"
    )
    # Keep completed assets and immutable submitted history. Abandoned mutable
    # revisions expire only when they are neither published nor processing.
    for revision in TourRevision.objects.filter(
        review_state="not_submitted",
        processing_state__in=["draft", "failed", "ready"],
        updated_at__lt=now - timedelta(days=30),
    ):
        if revision.tour.active_revision_id != revision.pk:
            revision.delete()
    referenced = set(TourAsset.objects.values_list("blob", flat=True))
    from .capture_models import (
        PropertyCaptureSession,
        CaptureAsset,
        CaptureProcessingJob,
    )

    PropertyCaptureSession.objects.filter(
        deleted_at=None,
        updated_at__lt=now - timedelta(days=settings.CAPTURE_RETENTION_DAYS),
    ).update(deleted_at=now, state="cancelled")
    CaptureProcessingJob.objects.filter(
        manifest__session__deleted_at__isnull=False
    ).update(cancel_requested=True)
    for capture in CaptureAsset.objects.filter(session__deleted_at=None):
        if capture.blob:
            referenced.add(capture.blob)
        referenced.update(p["blob"] for p in capture.parts.values())
    for outputs in CaptureProcessingJob.objects.filter(
        manifest__session__deleted_at=None
    ).values_list("outputs", flat=True):
        for station in outputs.get("panorama360", {}).get("stations", []):
            referenced.update(r["blob"] for r in station.get("resources", {}).values())
    for resources in TourVariant.objects.values_list("resources", flat=True):
        referenced.update(r["blob"] for r in resources.values())
    for parts in TourUploadSession.objects.filter(
        state="open", expires_at__gt=now
    ).values_list("parts", flat=True):
        referenced.update(p["blob"] for p in parts.values())
    threshold = (now - timedelta(days=7)).timestamp()
    removed = 0
    for entry in root().iterdir():
        if (
            entry.name not in referenced or remote_storage.configured()
        ) and entry.stat().st_mtime < threshold:
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
            removed += 1
    return {
        "removed_local_files": removed,
        "removed_remote_orphans": remote_storage.sweep(referenced, threshold),
    }
