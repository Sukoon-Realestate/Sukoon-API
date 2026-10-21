import hashlib
import io
import json
import uuid
from datetime import timedelta
from unittest.mock import patch
import pytest
from PIL import Image
from django.utils import timezone
from core_apps.virtual_tours.capture_models import (
    PropertyCaptureSession,
    CaptureAsset,
    CaptureManifestRevision,
    CaptureProcessingJob,
    CaptureCoachSession,
)
from core_apps.virtual_tours.capture_validation import frame, MODES, CONVENTION, POLICY
from core_apps.virtual_tours.errors import TourError
from core_apps.virtual_tours.capture_worker import claim, run
from core_apps.virtual_tours import storage


def uid():
    return str(uuid.uuid4())


def image_bytes():
    image = Image.effect_noise((640, 480), 60).convert("RGB")
    stream = io.BytesIO()
    image.save(stream, "JPEG", quality=95)
    return stream.getvalue()


def metadata(room, data, mode="walkthrough3d"):
    segment = uid()
    result = {
        "schemaVersion": 1,
        "frameId": uid(),
        "roomId": room,
        "trackingSegmentId": segment,
        "coordinateFrameId": segment,
        "captureMode": mode,
        "timestampMonotonicNs": "99999999999999999",
        "image": {
            "width": 640,
            "height": 480,
            "orientationApplied": "sensor_native",
            "sha256": hashlib.sha256(data).hexdigest(),
        },
        "camera": {
            "calibrationId": "test",
            "model": "pinhole",
            "fx": 500,
            "fy": 500,
            "cx": 320,
            "cy": 240,
            "physicalLensId": "test",
            "distortionHandling": "sdk_intrinsics_unverified",
        },
        "pose": {
            "convention": "T_world_camera_optical_row_major",
            "matrix": [1, 0, 0, 0, 0, -1, 0, 1.5, 0, 0, -1, 0, 0, 0, 0, 1],
            "trackingState": "tracking",
            "source": "arcore",
            "mapRevision": 0,
        },
        "quality": {
            "accepted": True,
            "policyVersion": POLICY,
            "syncOffsetMs": 0,
            "sharpness": 200,
            "darkFraction": 0.1,
            "clippedFraction": 0.1,
            "featureIds": [str(i) for i in range(20)],
        },
        "depth": None,
    }
    if mode == "panorama360":
        result["stationId"] = uid()
    return result


@pytest.fixture
def capture(settings, auth_client, property_obj):
    settings.PROPERTY_CAPTURE_ENABLED = True

    def post(path, body, key=None):
        return auth_client.post(
            "/api/v1/" + path, body, format="json", HTTP_IDEMPOTENCY_KEY=key or uid()
        )

    response = post(
        f"properties/{property_obj.id}/capture-sessions/",
        {
            "clientSessionId": uid(),
            "requestedOutputs": list(MODES),
            "capturePolicyVersion": POLICY,
            "coachOptIn": False,
        },
    )
    assert response.status_code == 201, response.data
    session = PropertyCaptureSession.objects.get(id=response.data["id"])
    base = f"property-captures/{session.id}/"
    room = uid()
    assert (
        post(
            base + "rooms/",
            {"id": room, "label": "Consented synthetic fixture", "confirmed": True},
        ).status_code
        == 200
    )
    return session, base, room, post


def upload(capture, auth_client, mode="walkthrough3d"):
    session, base, room, post = capture
    data = image_bytes()
    meta = metadata(room, data, mode)
    response = post(base + "uploads/", {"size": len(data), "metadata": meta})
    assert response.status_code == 201, response.data
    asset_path = base + f'uploads/{response.data["id"]}/'
    result = auth_client.put(
        "/api/v1/" + asset_path + "parts/1/",
        data,
        content_type="application/octet-stream",
    )
    assert result.status_code == 200, result.data
    result = post(asset_path + "complete/", {})
    assert result.status_code == 200, result.data
    return meta, asset_path, data


def finalize(capture, frames):
    session, base, room, post = capture
    doc = {
        "schemaVersion": 1,
        "sessionId": str(session.id),
        "propertyId": str(session.property.id),
        "requestedOutputs": list(MODES),
        "capturePolicyVersion": POLICY,
        "coordinateConvention": CONVENTION,
        "roomIds": [room],
        "frameIds": [f["frameId"] for f in frames],
    }
    return post(
        base + "manifests/", {"expectedRevision": session.revision, "document": doc}
    )


@pytest.mark.django_db
def test_scope_idempotency_and_no_public_blob(capture, auth_client, another_user):
    session, base, room, post = capture
    meta, path, data = upload(capture, auth_client)
    result = post(path + "complete/", {})
    assert result.data["state"] == "verified" and "blob" not in result.data
    assert result["Cache-Control"] == "private, no-store"
    assert "path" not in json.dumps(result.data)
    auth_client.force_authenticate(another_user)
    for resource in [base, path]:
        assert auth_client.get("/api/v1/" + resource).status_code == 404
    assert (
        post(
            base + "rooms/", {"id": uid(), "label": "Intruder", "confirmed": True}
        ).status_code
        == 404
    )


@pytest.mark.django_db
def test_real_bytes_checksum_and_part_conflict(capture, auth_client):
    session, base, room, post = capture
    data = image_bytes()
    meta = metadata(room, data)
    response = post(base + "uploads/", {"size": len(data), "metadata": meta})
    path = base + f'uploads/{response.data["id"]}/'
    assert post(path + "complete/", {}).status_code == 422
    bad = bytes([data[0] ^ 1]) + data[1:]
    assert (
        auth_client.put(
            "/api/v1/" + path + "parts/1/", bad, content_type="application/octet-stream"
        ).status_code
        == 200
    )
    assert post(path + "complete/", {}).status_code == 422
    assert CaptureAsset.objects.get(id=response.data["id"]).state == "open"
    assert (
        auth_client.put(
            "/api/v1/" + path + "parts/1/",
            data,
            content_type="application/octet-stream",
        ).status_code
        == 409
    )


@pytest.mark.django_db
def test_manifest_cross_session_and_immutable_job(capture, auth_client):
    session, base, room, post = capture
    meta, _, _ = upload(capture, auth_client)
    assert finalize(capture, [meta]).status_code == 201
    assert finalize(capture, [meta]).status_code == 200
    first = post(base + "processing-jobs/", {"manifestRevision": 1})
    retry = post(base + "processing-jobs/", {"manifestRevision": 1})
    assert first.status_code == 202 and first.data["id"] == retry.data["id"]
    assert CaptureProcessingJob.objects.count() == 1
    assert CaptureManifestRevision.objects.count() == 1
    assert finalize(capture, [dict(meta, frameId=uid())]).status_code == 422


@pytest.mark.django_db
def test_late_worker_cannot_publish_deleted_capture(capture, auth_client):
    session, base, room, post = capture
    meta, _, _ = upload(capture, auth_client)
    finalize(capture, [meta])
    post(base + "processing-jobs/", {"manifestRevision": 1})
    job = claim()
    assert job
    assert (
        auth_client.delete(
            "/api/v1/" + base, {}, format="json", HTTP_IDEMPOTENCY_KEY=uid()
        ).status_code
        == 200
    )
    run(job)
    job.refresh_from_db()
    assert job.state == "cancelled"
    assert all(v["status"] == "cancelled" for v in job.outputs.values())
    assert auth_client.get("/api/v1/" + base).status_code == 404


@pytest.mark.django_db
def test_stale_lease_fences_old_worker(capture, auth_client):
    session, base, room, post = capture
    meta, _, _ = upload(capture, auth_client)
    finalize(capture, [meta])
    post(base + "processing-jobs/", {"manifestRevision": 1})
    first = claim()
    CaptureProcessingJob.objects.filter(pk=first.pk).update(
        lease_until=timezone.now() - timedelta(seconds=1)
    )
    second = claim()
    run(first)
    second.refresh_from_db()
    assert second.lease_token != first.lease_token and second.state == "processing"


@pytest.mark.django_db
def test_coach_consent_budget_and_secret_never_persisted(capture, settings):
    settings.CAPTURE_COACH_PRIVATE_INPUTS_APPROVED = True
    session, base, room, post = capture
    assert post(base + "coach-sessions/", {}).status_code == 409
    session.state = "capturing"
    session.coach_opt_in = True
    session.save()
    with patch(
        "core_apps.virtual_tours.capture_coach.provision",
        return_value={
            "credential": "ephemeral-fixture",
            "transport": "gemini_live_direct",
        },
    ):
        response = post(base + "coach-sessions/", {})
        assert (
            response.status_code == 201
            and response.data["credential"] == "ephemeral-fixture"
        )
        assert post(base + "coach-sessions/", {}).status_code == 409
        record = CaptureCoachSession.objects.get(session=session)
        close_url = base + f"coach-sessions/{record.id}/close/"
        assert post(close_url, {}).status_code == 200
        assert post(close_url, {}).status_code == 200
        assert post(base + "coach-sessions/", {}).status_code == 201
        latest = CaptureCoachSession.objects.filter(session=session).latest('created_at')
        assert post(base + f"coach-sessions/{latest.id}/close/", {}).status_code == 200
        settings.COACH_DAILY_SESSION_LIMIT = 2
        assert post(base + "coach-sessions/", {}).status_code == 429
    assert "credential" not in [f.name for f in CaptureCoachSession._meta.fields]


@pytest.mark.parametrize(
    "change",
    [
        lambda m: m.update(timestampMonotonicNs=99999999999999999),
        lambda m: m["pose"]["matrix"].__setitem__(0, -1),
        lambda m: m["pose"]["matrix"].__setitem__(15, 0),
        lambda m: m["camera"].update(fx=float("nan")),
        lambda m: m["camera"].update(fx=1e300),
        lambda m: m["pose"]["matrix"].__setitem__(3, 1e300),
        lambda m: m["image"].update(path="../../secret"),
        lambda m: m["quality"].update(syncOffsetMs=300),
        lambda m: m["quality"].update(accepted=False),
        lambda m: m.update(depth={"url": "https://other-owner/"}),
        lambda m: m.update(captureMode="panorama360"),
    ],
)
def test_invalid_camera_evidence_is_rejected(change):
    m = metadata(uid(), b"fixture")
    change(m)
    with pytest.raises(TourError):
        frame(m)


@pytest.mark.django_db
def test_partial_panorama_does_not_become_full_tour(capture, auth_client):
    pytest.importorskip("cv2")
    session, base, room, post = capture
    meta, _, _ = upload(capture, auth_client, "panorama360")
    finalize(capture, [meta])
    post(base + "processing-jobs/", {"manifestRevision": 1})
    job = claim()
    run(job)
    job.refresh_from_db()
    station = job.outputs["panorama360"]["stations"][0]
    assert station["fullSphere"] is False and station["observedFraction"] < 0.5
    assert storage.read_path(station["resources"]["mask"]["blob"]).exists()
    assert job.outputs["walkthrough3d"] == {
        "status": "needsCapture",
        "code": "INSUFFICIENT_TRANSLATIONAL_VIEWS",
        "components": [],
    }
    assert job.state == "needs_capture"


@pytest.mark.django_db
def test_multipart_resume_and_missing_parts(capture, auth_client):
    _, base, room, post = capture
    stream = io.BytesIO()
    Image.effect_noise((2000, 1600), 70).convert("RGB").save(stream, "JPEG", quality=98)
    data = stream.getvalue()
    assert len(data) > 1024**2
    meta = metadata(room, data)
    meta["image"].update(width=2000, height=1600)
    meta["camera"].update(fx=1400, fy=1400, cx=1000, cy=800)
    reserved = post(base + "uploads/", {"size": len(data), "metadata": meta})
    assert reserved.status_code == 201
    path = base + f'uploads/{reserved.data["id"]}/'
    size = reserved.data["partBytes"]
    for index in range(1, (len(data) + size - 1) // size + 1):
        part = data[(index - 1) * size : index * size]
        response = auth_client.put(
            "/api/v1/" + path + f"parts/{index}/",
            part,
            content_type="application/octet-stream",
        )
        assert response.status_code == 200
        # A new request after a connection loss discovers durable progress.
        status = auth_client.get("/api/v1/" + path)
        assert status.data["receivedParts"] == list(range(1, index + 1))
        if index == 1:
            assert post(path + "complete/", {}).status_code == 422
            assert (
                auth_client.put(
                    "/api/v1/" + path + "parts/1/",
                    part,
                    content_type="application/octet-stream",
                ).status_code
                == 200
            )
    assert post(path + "complete/", {}).data["state"] == "verified"


@pytest.mark.django_db
def test_private_generated_image_requires_owner_and_keeps_blob_internal(
    capture, auth_client, another_user
):
    session, base, _, post = capture
    meta, _, _ = upload(capture, auth_client, "panorama360")
    finalize(capture, [meta])
    job_id = post(base + "processing-jobs/", {"manifestRevision": 1}).data["id"]
    job = CaptureProcessingJob.objects.get(id=job_id)
    blob, size, checksum = storage.write_blob([b"private-png-fixture"], 100)
    job.outputs = {
        "panorama360": {
            "status": "needsCapture",
            "stations": [
                {
                    "id": meta["stationId"],
                    "fullSphere": False,
                    "resources": {
                        "image": {
                            "blob": blob,
                            "size": size,
                            "sha256": checksum,
                            "mediaType": "image/png",
                        }
                    },
                }
            ],
        }
    }
    job.save()
    payload = auth_client.get("/api/v1/" + base).data
    serialized = json.dumps(payload)
    assert blob not in serialized and '"blob"' not in serialized
    path = payload["jobs"][0]["outputs"]["panorama360"]["stations"][0]["resources"][
        "image"
    ]["path"]
    response = auth_client.get("/api/v1/" + path)
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    assert b"".join(response.streaming_content) == b"private-png-fixture"
    auth_client.force_authenticate(another_user)
    assert auth_client.get("/api/v1/" + path).status_code == 404
    assert (
        auth_client.get("/api/v1/" + base + f"processing-jobs/{job_id}/").status_code
        == 404
    )
    auth_client.force_authenticate(session.owner)
    post(base + f"processing-jobs/{job_id}/", {})
    assert auth_client.get("/api/v1/" + path).status_code == 404


@pytest.mark.django_db
def test_private_reconstruction_preview_requires_owner_and_keeps_blob_internal(
    capture, auth_client, another_user
):
    session, base, _, post = capture
    meta, _, _ = upload(capture, auth_client)
    finalize(capture, [meta])
    job_id = post(base + "processing-jobs/", {"manifestRevision": 1}).data["id"]
    job = CaptureProcessingJob.objects.get(id=job_id)
    component_id = uid()
    blob, size, checksum = storage.write_blob([b"private-preview"], 100)
    job.outputs = {
        "walkthrough3d": {
            "status": "needsReview",
            "components": [{
                "id": component_id,
                "resources": {
                    "thumbnail": {
                        "blob": blob, "size": size, "sha256": checksum,
                        "mediaType": "image/jpeg",
                    }
                },
            }],
        }
    }
    job.save()
    serialized = json.dumps(auth_client.get("/api/v1/" + base).data)
    assert blob not in serialized and '"blob"' not in serialized
    path = (
        base + f"processing-jobs/{job_id}/components/{component_id}/thumbnail/"
    )
    response = auth_client.get("/api/v1/" + path)
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    assert b"".join(response.streaming_content) == b"private-preview"
    auth_client.force_authenticate(another_user)
    assert auth_client.get("/api/v1/" + path).status_code == 404
    auth_client.force_authenticate(session.owner)
    post(base + f"processing-jobs/{job_id}/", {})
    assert auth_client.get("/api/v1/" + path).status_code == 404


@pytest.mark.django_db
def test_crashing_jobs_have_a_finite_retry_budget(capture, auth_client):
    _, base, _, post = capture
    meta, _, _ = upload(capture, auth_client)
    finalize(capture, [meta])
    job_id = post(base + "processing-jobs/", {"manifestRevision": 1}).data["id"]
    for attempt in range(1, 4):
        job = claim()
        assert job.attempt == attempt
        CaptureProcessingJob.objects.filter(id=job_id).update(
            lease_until=timezone.now() - timedelta(seconds=1)
        )
    assert claim() is None
    job.refresh_from_db()
    assert job.state == "failed"
    assert job.outputs["walkthrough3d"]["code"] == "PROCESSING_RETRY_EXHAUSTED"


@pytest.mark.django_db
def test_disabled_capture_blocks_new_cost_but_allows_status_and_cancellation(
    capture, auth_client, settings
):
    _, base, room, post = capture
    meta, _, _ = upload(capture, auth_client)
    finalize(capture, [meta])
    job_id = post(base + "processing-jobs/", {"manifestRevision": 1}).data["id"]
    settings.PROPERTY_CAPTURE_ENABLED = False
    data = image_bytes()
    assert (
        post(
            base + "uploads/", {"size": len(data), "metadata": metadata(room, data)}
        ).status_code
        == 503
    )
    assert post(base + "processing-jobs/", {"manifestRevision": 1}).status_code == 503
    assert auth_client.get("/api/v1/" + base).status_code == 200
    assert post(base + f"processing-jobs/{job_id}/", {}).status_code == 200


@pytest.mark.django_db(transaction=True)
def test_postgres_capture_reservations_and_worker_claims_are_exclusive(
    capture, auth_client
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connection, close_old_connections
    from rest_framework.test import APIClient

    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locking")
    session, base, room, post = capture
    data = image_bytes()
    meta = metadata(room, data)
    barrier = Barrier(2)

    def reserve_concurrently(index):
        close_old_connections()
        try:
            client = APIClient()
            client.force_authenticate(session.owner)
            barrier.wait(timeout=10)
            response = client.post(
                "/api/v1/" + base + "uploads/",
                {"size": len(data), "metadata": meta},
                format="json",
                HTTP_IDEMPOTENCY_KEY=f"capture-concurrent-{index}",
            )
            return response.status_code, response.data["id"]
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve_concurrently, range(2)))
    assert sorted(r[0] for r in results) == [200, 201]
    assert len({r[1] for r in results}) == 1
    assert CaptureAsset.objects.filter(session=session).count() == 1
    path = base + f"uploads/{results[0][1]}/"
    assert (
        auth_client.put(
            "/api/v1/" + path + "parts/1/",
            data,
            content_type="application/octet-stream",
        ).status_code
        == 200
    )
    assert post(path + "complete/", {}).status_code == 200
    assert finalize(capture, [meta]).status_code == 201
    post(base + "processing-jobs/", {"manifestRevision": 1})
    barrier = Barrier(2)

    def claim_concurrently(_):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            job = claim()
            return str(job.id) if job else None
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(claim_concurrently, range(2)))
    assert sum(value is not None for value in claims) == 1
    assert CaptureProcessingJob.objects.get().attempt == 1
