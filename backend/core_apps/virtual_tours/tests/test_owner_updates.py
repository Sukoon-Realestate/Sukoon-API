"""Real DB event/outbox integration; reconstruction and FCM remain simulated."""

from datetime import timedelta
from unittest.mock import patch
import uuid
import pytest
from django.db import transaction
from django.utils import timezone
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.notifications.models import DeviceToken, PushDelivery
from core_apps.notifications.services.push_delivery import dispatch
from core_apps.virtual_tours import notifications, processing, services, capture_worker
from core_apps.virtual_tours.models import TourRevision
from core_apps.virtual_tours.capture_models import (
    PropertyCaptureSession,
    CaptureManifestRevision,
    CaptureProcessingJob,
)
from . import test_tours as fixtures
from . import test_processing_lease as lease_fixtures

pytestmark = pytest.mark.django_db
SEND = "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device"


def detail(client, event):
    return client.get(f"/api/v1/virtual-tour-updates/{event.id}/")


def test_old_update_reads_current_tour_and_original_revision(
    auth_client, property_obj, superuser
):
    tour, revision, _ = fixtures.ready_variant(property_obj)
    first = notifications.record_tour(revision, "ready", "original")
    revision.review_state = "pending"
    revision.save()
    with transaction.atomic():
        services.review(
            revision,
            superuser,
            {
                "decision": "rejected",
                "expected_source_hash": revision.source_hash,
                "reason": "Private reviewer detail",
            },
        )
    newer = TourRevision.objects.create(tour=tour)
    response = detail(auth_client, first)
    assert response.status_code == 200, response.data
    assert response.data["revision"]["id"] == str(revision.id)
    assert response.data["revision"]["review_state"] == "rejected"
    assert response.data["tour"]["latest_revision"]["id"] == str(newer.id)
    assert [h["change"] for h in response.data["history"]] == ["rejected", "ready"]
    assert "Private reviewer detail" not in str(response.data)


@pytest.mark.parametrize("revocation", ["owner", "retired", "deleted", "target"])
def test_outbox_retry_rechecks_owner_and_exact_source(
    auth_client, property_obj, user, another_user, revocation
):
    tour, revision, _ = fixtures.ready_variant(property_obj)
    event = notifications.record_tour(revision, "ready", "original")
    DeviceToken.objects.create(user=user, token="synthetic-tour-device")
    with patch(SEND) as send:
        assert deliver_planning_events() == 1
        send.assert_not_called()
    with patch(SEND, return_value=False):
        assert dispatch() == 0
    if revocation == "owner":
        type(property_obj).objects.filter(pk=property_obj.pk).update(owner=another_user)
    elif revocation == "retired":
        type(property_obj).objects.filter(pk=property_obj.pk).update(
            retired_at=timezone.now(), status="hidden"
        )
    elif revocation == "deleted":
        tour.deleted = True
        tour.save()
    else:
        event.destination["revision_id"] = str(uuid.uuid4())
        event.save()
    PushDelivery.objects.update(next_attempt_at=timezone.now() - timedelta(seconds=1))
    with patch(SEND) as send:
        assert dispatch() == 0
        send.assert_not_called()
    assert PushDelivery.objects.get().suppressed
    response = detail(auth_client, event)
    if revocation == "deleted":
        assert response.status_code == 200 and response.data["available"] is False
    else:
        assert response.status_code == 404


def test_result_and_event_rollback_together_and_repeated_worker_no_duplicate(
    property_obj,
):
    revision = lease_fixtures.queued_revision(property_obj)
    variants = [
        {
            "context": "overview",
            "scope_fingerprint": "scope",
            "source_hash": revision.source_hash,
            "manifest": {},
            "resources": {},
        }
    ]
    with patch.object(
        processing, "build_variants", return_value=variants
    ), patch.object(
        notifications, "record_tour", side_effect=RuntimeError("outbox offline")
    ):
        with pytest.raises(RuntimeError):
            processing.process_revision(str(revision.id), revision.source_hash)
    revision.refresh_from_db()
    assert revision.processing_state == "processing"
    assert not revision.variants.exists() and not PlanningEvent.objects.exists()
    revision.processing_state = "queued"
    revision.save()
    with patch.object(processing, "build_variants", return_value=variants):
        processing.process_revision(str(revision.id), revision.source_hash)
        processing.process_revision(str(revision.id), revision.source_hash)
    assert PlanningEvent.objects.count() == revision.variants.count() == 1


def capture_job(property_obj, user):
    session = PropertyCaptureSession.objects.create(
        property=property_obj, owner=user, client_id=uuid.uuid4()
    )
    manifest = CaptureManifestRevision.objects.create(
        session=session, revision=1, sha256="a" * 64, document={"frameIds": []}
    )
    return CaptureProcessingJob.objects.create(manifest=manifest)


def test_capture_result_keeps_manifest_and_job_no_implicit_3d_success(
    auth_client, property_obj, user, another_user
):
    job = capture_job(property_obj, user)
    claimed = capture_worker.claim()
    with patch.object(
        capture_worker.capture_panorama,
        "process",
        return_value={"status": "needsCapture", "stations": []},
    ), patch.object(
        capture_worker.capture_reconstruction,
        "process",
        return_value={
            "status": "needsProcessing",
            "code": "GPU_RUNTIME_NOT_CONFIGURED",
        },
    ):
        capture_worker.run(claimed)
        capture_worker.run(claimed)
    event = PlanningEvent.objects.get()
    response = detail(auth_client, event)
    assert response.status_code == 200, response.data
    assert response.data["job"]["id"] == str(job.id)
    assert response.data["job"]["manifestRevision"] == 1
    assert (
        response.data["job"]["outputs"]["walkthrough3d"]["status"] == "needsProcessing"
    )
    assert not TourRevision.objects.exists()
    auth_client.force_authenticate(another_user)
    assert detail(auth_client, event).status_code == 404


def test_final_cancellation_after_heartbeat_fences_result(property_obj, user):
    job = capture_job(property_obj, user)
    claimed = capture_worker.claim()

    # Simulate cancellation committed after the final heartbeat, before commit.
    def result(*args):
        CaptureProcessingJob.objects.filter(pk=job.pk).update(cancel_requested=True)
        return {"status": "needsReview", "components": []}

    with patch.object(
        capture_worker.capture_panorama, "process", return_value={}
    ), patch.object(
        capture_worker.capture_reconstruction, "process", side_effect=result
    ):
        capture_worker.run(claimed)
    job.refresh_from_db()
    assert job.state == "cancelled" and job.lease_token is None
    assert PlanningEvent.objects.get().destination["change"] == "capture_cancelled"


def test_exhausted_worker_creates_one_followup(property_obj, user):
    job = capture_job(property_obj, user)
    job.state, job.attempt, job.lease_until = (
        "processing",
        3,
        timezone.now() - timedelta(seconds=1),
    )
    job.save()
    assert capture_worker.claim() is None
    assert capture_worker.claim() is None
    assert PlanningEvent.objects.get().destination["change"] == "capture_failed"
