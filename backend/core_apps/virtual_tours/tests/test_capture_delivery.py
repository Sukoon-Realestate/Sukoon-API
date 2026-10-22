import copy
import io
import json
import struct
import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from core_apps.virtual_tours import services, sessions, storage
from core_apps.virtual_tours.capture_models import CaptureManifestRevision, CaptureProcessingJob, CaptureRoom, PropertyCaptureSession
from core_apps.virtual_tours.capture_delivery import build_variants, gaussian_count, validate
from core_apps.virtual_tours.errors import TourError
from core_apps.virtual_tours.models import PropertyVirtualTour, TourRevision
from core_apps.virtual_tours.processing import process_revision
from core_apps.virtual_tours.tasks import cleanup_tours


def identity():
    return str(uuid.uuid4())


def blob(data, mime="application/json"):
    key, size, checksum = storage.write_blob([data], 32 * 1024**2)
    return {"blob": key, "size": size, "sha256": checksum, "mediaType": mime}


def ply():
    names = "x y z nx ny nz f_dc_0 f_dc_1 f_dc_2 opacity scale_0 scale_1 scale_2 rot_0 rot_1 rot_2 rot_3".split()
    header = "ply\nformat binary_little_endian 1.0\nelement vertex 1\n" + "".join(f"property float {n}\n" for n in names) + "end_header\n"
    return header.encode() + struct.pack("<17f", 0, 1, -2, 0, 0, 0, 0, 0, 0, 1, -2, -2, -2, 1, 0, 0, 0)


@pytest.fixture
def selected_job(property_obj, user, settings):
    settings.PROPERTY_CAPTURE_ENABLED = True
    settings.VIRTUAL_TOUR_PROCESSOR_MODE = "polling"
    settings.VIRTUAL_TOUR_GLTF_VALIDATOR = ["test-validator"]
    settings.VIRTUAL_TOUR_SPAWN_VALIDATOR = ["test-validator"]
    session = PropertyCaptureSession.objects.create(property=property_obj, owner=user, client_id=uuid.uuid4())
    room, component, camera, station = [identity() for _ in range(4)]
    CaptureRoom.objects.create(session=session, client_id=room, label="Synthetic room, not a real property scan", confirmed=True)
    manifest = CaptureManifestRevision.objects.create(session=session, revision=1, sha256="a" * 64, document={"frameIds": [], "roomIds": [room]})
    pose = [1, 0, 0, 0, 0, -1, 0, 1.55, 0, 0, -1, 0, 0, 0, 0, 1]
    transform = [1, 0, 0, 0, 0, 1, 0, 1.55, 0, 0, 1, 0, 0, 0, 0, 1]
    encoded = io.BytesIO(); Image.new("RGB", (2048, 1024), (80, 130, 150)).save(encoded, "PNG")
    gaussian = blob(ply(), "application/octet-stream")
    outputs = {"walkthrough3d": {"components": [{"id": component, "roomIds": [room], "status": "needsReview", "scaleStatus": "validated_metric",
        "defaultCameraId": camera, "navigationStatus": "needsReview", "quality": {"appearanceValidated": True},
        "stationToSceneTransforms": {station: {"status": "validated", "matrix": transform}},
        "resources": {"preview": gaussian, "detail": gaussian,
            "cameras": blob(json.dumps([{"id": camera, "roomId": room, "cameraToWorld": pose}]).encode()),
            "navigation": blob(json.dumps({"status": "needsReview", "cells": []}).encode())}}]},
        "panorama360": {"stations": [{"id": station, "roomId": room, "status": "needsReview", "fullSphere": True,
            "resources": {"image": blob(encoded.getvalue(), "image/png")}}]}}
    job = CaptureProcessingJob.objects.create(manifest=manifest, state="needs_capture", outputs=outputs)
    document = {"schema_version": 2, "representation": "capture_derived", "kind": "model_3d",
        "title": {"ar": "بيانات اختبار اصطناعية", "en": "Synthetic capture test"},
        "captured_at": manifest.created_at.date().isoformat(), "content_origin": "reality_scan",
        "spaces": [{"id": room, "label": {"ar": "اختبار", "en": "Test"}, "floor_id": "ground", "space_kind": "room"}],
        "component_ids": [component], "station_ids": [station], "hotspots": [],
        "variants": [{"context": "overview", "space_ids": [room], "component_ids": [component], "station_ids": [station], "start_place_id": component}]}
    return job, document


@pytest.mark.django_db
def test_selection_private_preview_version_negotiation_review_and_revocation(selected_job, auth_client, user, another_user):
    job, document = selected_job
    path = f"/api/v1/property-captures/{job.manifest.session.id}/processing-jobs/{job.id}/select-outputs/"
    body = {"authoring": document, "expectedManifestHash": job.manifest.sha256}
    key = identity()
    first = auth_client.post(path, body, format="json", HTTP_IDEMPOTENCY_KEY=key)
    assert first.status_code == 202, first.data
    replay = auth_client.post(path, body, format="json", HTTP_IDEMPOTENCY_KEY=key)
    assert replay.data["id"] == first.data["id"]
    assert TourRevision.objects.count() == 1
    revision = TourRevision.objects.get(id=first.data["id"])
    process_revision(revision.id, revision.source_hash); revision.refresh_from_db()
    assert revision.processing_state == "ready", revision.report
    assert revision.tour.active_revision_id is None
    with pytest.raises(TourError, match="Update the app"):
        sessions.create_session(revision.tour, user, {"preview": True, "revision_id": str(revision.id)})
    opened = sessions.create_session(revision.tour, user, {"preview": True, "revision_id": str(revision.id), "supported_manifest_versions": [1, 2]})
    client = APIClient()
    response = client.post("/api/v1/virtual-tour-viewer/exchange/", {"bootstrap_token": opened["bootstrap_token"]}, format="json")
    assert response.status_code == 200
    token = response.data["credential"]
    url = f'/api/v1/virtual-tour-viewer/sessions/{opened["session_id"]}/'
    result = client.get(url + "manifest/", HTTP_X_TOUR_CREDENTIAL=token)
    assert result.status_code == 200 and result.data["schema_version"] == 2
    assert "blob" not in json.dumps(result.data)
    assert len(result.data["alignments"]) == 1
    with pytest.raises(TourError): sessions.create_session(revision.tour, another_user, {"preview": True, "revision_id": str(revision.id), "supported_manifest_versions": [2]})
    services.submit_review(revision, {"source_hash": revision.source_hash}, '"draft-1"')
    assert revision.review_state == "pending"
    # Even an administrator cannot independently approve their own capture.
    user.is_staff = True
    with patch.object(user, "has_perm", return_value=True):
        with pytest.raises(TourError, match="different authorized reviewer"):
            services.review(revision, user, {"decision": "approved", "expected_source_hash": revision.source_hash, "reason": "Self review is invalid"})
    revision.refresh_from_db()
    assert revision.review_state == "pending"
    job.cancel_requested = True; job.save(update_fields=["cancel_requested"])
    assert client.get(url + "manifest/", HTTP_X_TOUR_CREDENTIAL=token).status_code == 409


@pytest.mark.django_db
def test_scope_cannot_crop_a_component_and_incomplete_panorama_is_rejected(selected_job):
    job, document = selected_job
    tour = PropertyVirtualTour.objects.create(property=job.manifest.session.property, kind="model_3d")
    revision = TourRevision(tour=tour, capture_job=job, authoring=document)
    job.outputs["walkthrough3d"]["components"][0]["roomIds"].append(identity())
    with pytest.raises(TourError, match="Map every captured room"): validate(revision, document)
    job.outputs["walkthrough3d"]["components"][0]["roomIds"].pop()
    job.outputs["panorama360"]["stations"][0]["fullSphere"] = False
    with pytest.raises(TourError, match="Incomplete spheres"): validate(revision, document)


@pytest.mark.django_db
def test_bad_quality_can_be_previewed_but_not_submitted_and_no_fake_walk(selected_job):
    job, document = selected_job
    tour = PropertyVirtualTour.objects.create(property=job.manifest.session.property, kind="model_3d")
    job.outputs["walkthrough3d"]["components"][0]["quality"]["appearanceValidated"] = False
    job.save(update_fields=["outputs"])
    revision = TourRevision.objects.create(tour=tour, capture_job=job, authoring=document)
    revision.source_hash, _ = validate(revision, document)
    assert build_variants(revision)[0]["manifest"]["components"][0]["navigation_status"] == "needsReview"
    with pytest.raises(TourError, match="quality check"):
        services.submit_review(revision, {"source_hash": revision.source_hash}, '"draft-1"')
    job.outputs["walkthrough3d"]["components"][0]["navigationStatus"] = "validated"
    revision.source_hash, _ = validate(revision, document)
    with pytest.raises(TourError, match="Navigation evidence"): build_variants(revision)


@pytest.mark.django_db
def test_gaussian_integrity_and_retention(selected_job, settings):
    job, document = selected_job
    resource = job.outputs["walkthrough3d"]["components"][0]["resources"]["preview"]
    assert gaussian_count(resource, 20000) == 1
    wrong = {**resource, "sha256": "0" * 64}
    with pytest.raises(TourError, match="checksum"): gaussian_count(wrong, 20000)
    tour = PropertyVirtualTour.objects.create(property=job.manifest.session.property, kind="model_3d")
    revision = TourRevision.objects.create(tour=tour, capture_job=job, authoring=document, review_state="pending")
    PropertyCaptureSession.objects.filter(pk=job.manifest.session_id).update(updated_at=timezone.now() - timedelta(days=400))
    with patch("core_apps.virtual_tours.tasks.remote_storage.sweep", return_value=0) as sweep:
        cleanup_tours.run()
        assert resource["blob"] in sweep.call_args.args[0]
    job.manifest.session.refresh_from_db()
    assert job.manifest.session.deleted_at is None
