from datetime import timedelta
from unittest.mock import patch
import uuid

import pytest
from django.utils import timezone

from core_apps.virtual_tours import processing, tasks
from core_apps.virtual_tours.models import TourRevision
from core_apps.virtual_tours.processing_lease import (
    ProcessingLease,
    ProcessingSuperseded,
)
from core_apps.virtual_tours.validation import validate_authoring
from .test_tours import synthetic_draft


pytestmark = pytest.mark.django_db


def queued_revision(property_obj):
    _, revision, _ = synthetic_draft(property_obj)
    revision.source_hash, _ = validate_authoring(revision, revision.authoring)
    revision.processing_state = "queued"
    revision.save()
    return revision


@pytest.mark.parametrize("old_attempt_fails", [False, True])
def test_reclaimed_attempt_cannot_publish_or_fail_new_worker(
    property_obj, old_attempt_fails
):
    revision = queued_revision(property_obj)
    replacement_token = uuid.uuid4()

    def interrupted_build(claimed, heartbeat):
        heartbeat()
        TourRevision.objects.filter(pk=claimed.pk).update(
            updated_at=timezone.now() - timedelta(minutes=21)
        )
        tasks.recover_interrupted_tours()
        # The replacement worker has claimed this same immutable source, but
        # has not finished. The original worker returns late after reconnecting.
        TourRevision.objects.filter(pk=claimed.pk).update(
            processing_state="processing", processing_token=replacement_token,
            stage="replacement_attempt", report={"worker_recoveries": 1},
        )
        if old_attempt_fails:
            raise RuntimeError("An old provider response failed")
        return [{
            "context": "overview", "scope_fingerprint": "scope",
            "source_hash": claimed.source_hash, "manifest": {"old": True},
            "resources": {},
        }]

    with patch.object(processing, "build_variants", side_effect=interrupted_build):
        processing.process_revision(str(revision.id), revision.source_hash)
    revision.refresh_from_db()
    assert revision.processing_state == "processing"
    assert revision.processing_token == replacement_token
    assert revision.stage == "replacement_attempt"
    assert revision.report == {"worker_recoveries": 1}
    assert not revision.variants.exists()


def test_progress_renews_lease_and_stale_worker_stops_after_recovery(property_obj):
    revision = queued_revision(property_obj)
    revision.processing_state = "processing"
    revision.processing_token = uuid.uuid4()
    revision.save()
    lease = ProcessingLease(revision)
    rows = TourRevision.objects.filter(pk=revision.pk)
    rows.update(updated_at=timezone.now() - timedelta(minutes=21))
    lease.heartbeat()
    tasks.recover_interrupted_tours()
    revision.refresh_from_db()
    assert revision.processing_state == "processing"
    assert revision.processing_token == lease.token

    rows.update(updated_at=timezone.now() - timedelta(minutes=21))
    tasks.recover_interrupted_tours()
    revision.refresh_from_db()
    assert revision.processing_state == "queued"
    assert revision.processing_token is None
    assert revision.stage == "queued"
    assert revision.report["worker_recoveries"] == 1
    lease.next_heartbeat = 0
    with pytest.raises(ProcessingSuperseded):
        lease.heartbeat()


def test_interruption_attempts_remain_bounded(property_obj):
    revision = queued_revision(property_obj)
    rows = TourRevision.objects.filter(pk=revision.pk)
    for attempt in range(1, 5):
        rows.update(
            processing_state="processing", processing_token=uuid.uuid4(),
            updated_at=timezone.now() - timedelta(minutes=21),
        )
        tasks.recover_interrupted_tours()
        revision.refresh_from_db()
        assert revision.processing_state == ("queued" if attempt <= 3 else "failed")
        assert revision.processing_token is None
        assert revision.report["worker_recoveries"] == attempt
        assert revision.updated_at > timezone.now() - timedelta(minutes=1)


def test_current_attempt_completes_once_and_clears_lease(property_obj):
    revision = queued_revision(property_obj)
    revision.report = {"worker_recoveries": 2, "code": "worker_interrupted"}
    revision.save()

    def build(claimed, heartbeat):
        heartbeat()
        assert claimed.report == {"worker_recoveries": 2}
        return [{
            "context": "overview", "scope_fingerprint": "scope",
            "source_hash": claimed.source_hash, "manifest": {}, "resources": {},
        }]

    with patch.object(processing, "build_variants", side_effect=build) as builder:
        processing.process_revision(str(revision.id), revision.source_hash)
        processing.process_revision(str(revision.id), revision.source_hash)
    revision.refresh_from_db()
    assert builder.call_count == 1
    assert revision.processing_state == "ready"
    assert revision.processing_token is None
    assert revision.variants.count() == 1
