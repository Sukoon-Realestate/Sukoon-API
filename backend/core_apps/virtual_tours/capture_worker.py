"""Durable polling worker; attempt ownership fences late or cancelled results."""

import time
import uuid
from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .capture_models import CaptureProcessingJob, CaptureAsset
from .capture_validation import MODES
from . import capture_panorama, capture_reconstruction


def claim():
    now = timezone.now()
    with transaction.atomic():
        # A repeatedly crashing worker must not spend an unbounded job budget.
        exhausted = CaptureProcessingJob.objects.filter(
            state="processing", lease_until__lt=now, attempt__gte=3
        )
        exhausted.update(
            state="failed",
            stage="attempts_exhausted",
            lease_token=None,
            lease_until=None,
            outputs={
                mode: {"status": "failed", "code": "PROCESSING_RETRY_EXHAUSTED"}
                for mode in MODES
            },
        )
        job = (
            CaptureProcessingJob.objects.select_for_update(skip_locked=True)
            .filter(Q(state="queued") | Q(state="processing", lease_until__lt=now))
            .filter(attempt__lt=3)
            .order_by("created_at")
            .first()
        )
        if not job:
            return None
        job.lease_token = uuid.uuid4()
        job.lease_until = now + timedelta(seconds=90)
        job.attempt += 1
        job.state = "processing"
        job.stage = "validating_inputs"
        job.save()
        return job


def run(job):
    started = time.monotonic()
    # Projection and reconstruction share a lease, but reconstruction has its
    # own explicit hour budget. The old fixed 15 min cutoff cancelled it early.
    budget = 900 + capture_reconstruction.configuration()["seconds"]
    token = job.lease_token

    def cancelled():
        with transaction.atomic():
            current = (
                CaptureProcessingJob.objects.select_for_update()
                .select_related("manifest__session__property")
                .get(pk=job.pk)
            )
            stopped = (
                current.lease_token != token
                or current.cancel_requested
                or current.manifest.session.deleted_at is not None
                or current.manifest.session.property.retired_at is not None
                or current.manifest.session.property.owner_id
                != current.manifest.session.owner_id
                or time.monotonic() - started > budget
            )
            if not stopped:
                current.lease_until = timezone.now() + timedelta(seconds=90)
                current.save(update_fields=["lease_until"])
            return stopped

    outputs = {
        mode: {"status": "cancelled", "code": "PROCESSING_CANCELLED"} for mode in MODES
    }
    if not cancelled():
        assets = list(
            CaptureAsset.objects.filter(
                session=job.manifest.session,
                client_id__in=job.manifest.document["frameIds"],
                state="verified",
            )
        )
        CaptureProcessingJob.objects.filter(pk=job.pk, lease_token=token).update(
            stage="building_panorama"
        )
        try:
            outputs["panorama360"] = capture_panorama.process(assets, cancelled)
        except Exception:
            outputs["panorama360"] = {
                "status": "failed",
                "code": "PANORAMA_STITCH_FAILED",
            }
        if not cancelled():
            CaptureProcessingJob.objects.filter(pk=job.pk, lease_token=token).update(
                stage="building_3d"
            )
            if sum(a.metadata["captureMode"] == "walkthrough3d" for a in assets) < 8:
                outputs["walkthrough3d"] = capture_reconstruction.process(
                    assets, cancelled, lambda _stage: None
                )
            else:
                runtime = capture_reconstruction.runtime_status()
                if not runtime["available"]:
                    outputs["walkthrough3d"] = {
                        "status": "needsProcessing",
                        "code": runtime["code"],
                        "previewAvailable": False,
                    }
                else:
                    def progress(stage):
                        CaptureProcessingJob.objects.filter(
                            pk=job.pk, lease_token=token
                        ).update(
                            stage=stage,
                            lease_until=timezone.now() + timedelta(seconds=90),
                        )

                    try:
                        outputs["walkthrough3d"] = capture_reconstruction.process(
                            assets, cancelled, progress
                        )
                    except Exception:
                        outputs["walkthrough3d"] = {
                            "status": "failed",
                            "code": "RECONSTRUCTION_RUNTIME_FAILED",
                            "previewAvailable": False,
                        }
    stopped = cancelled()
    if stopped:
        outputs = {
            mode: {"status": "cancelled", "code": "PROCESSING_CANCELLED"}
            for mode in MODES
        }
    # No selected/public artifact is overwritten, including when a newer input
    # revision exists. Results always remain attached to their immutable input.
    CaptureProcessingJob.objects.filter(pk=job.pk, lease_token=token).update(
        state="cancelled" if stopped else "needs_capture",
        stage="cancelled" if stopped else "review_results",
        outputs=outputs,
        lease_until=None,
        diagnostics={
            "elapsedSeconds": round(time.monotonic() - started, 3),
            "engine": "calibrated-panorama-and-colmap-gsplat-v2",
            "releaseValidated": False,
        },
    )
