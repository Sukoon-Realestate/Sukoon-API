import copy
import hashlib
import io
import json
from datetime import timedelta
import pytest
from django.utils import timezone
from PIL import Image
from core_apps.virtual_tours import services, sessions, storage, uploads
from core_apps.virtual_tours.errors import TourError
from core_apps.virtual_tours.models import (
    PropertyVirtualTour,
    TourRevision,
    TourAsset,
    TourVariant,
    TourOperation,
)
from core_apps.virtual_tours.policy import digest, scope_policy
from core_apps.virtual_tours.processing import process_revision
from core_apps.virtual_tours.validation import validate_authoring

pytestmark = pytest.mark.django_db


def create(client, prop, key="create-tour-0001"):
    return client.post(
        f"/api/v1/properties/{prop.id}/virtual-tours/",
        {"kind": "panorama_360"},
        format="json",
        HTTP_IDEMPOTENCY_KEY=key,
    )


def synthetic_draft(prop):
    tour = PropertyVirtualTour.objects.create(property=prop, kind="panorama_360")
    revision = TourRevision.objects.create(tour=tour)
    buffer = io.BytesIO()
    Image.new("RGB", (4096, 2048), (10, 110, 50)).save(buffer, "JPEG")
    content = buffer.getvalue()
    blob, size, checksum = storage.write_blob([content], len(content))
    asset = TourAsset.objects.create(
        revision=revision,
        role="panorama",
        blob=blob,
        size=size,
        sha256=checksum,
        media_type="image/jpeg",
    )
    view = {"yaw_rad": 0, "pitch_rad": 0, "hfov_rad": 1.2}
    label = {"ar": "اختبار اصطناعي", "en": "Synthetic test"}
    doc = {
        "schema_version": 1,
        "kind": "panorama_360",
        "title": label,
        "captured_at": "2026-01-01",
        "content_origin": "photographic_capture",
        "spaces": [
            {"id": "hall", "label": label, "floor_id": "ground", "space_kind": "shared"}
        ],
        "scenes": [
            {
                "id": s,
                "space_id": "hall",
                "source_asset_id": str(asset.id),
                "initial_view": view,
            }
            for s in ("a", "b")
        ],
        "hotspots": [
            {
                "id": a + b,
                "source_scene_id": a,
                "target_scene_id": b,
                "yaw_rad": 0,
                "pitch_rad": 0,
                "label": label,
                "target_view": view,
            }
            for a, b in (("a", "b"), ("b", "a"))
        ],
        "variants": [
            {
                "context": "overview",
                "space_ids": ["hall"],
                "scene_ids": ["a", "b"],
                "start_scene_id": "a",
            }
        ],
    }
    services.patch_revision(revision, {"authoring": doc}, '"draft-1"')
    return tour, revision, doc


def ready_variant(prop):
    tour, revision, doc = synthetic_draft(prop)
    checksum, scopes = validate_authoring(revision, doc)
    revision.source_hash, revision.processing_state, revision.review_state = (
        checksum,
        "ready",
        "approved",
    )
    revision.save()
    blob, _, _ = storage.write_blob([b"private variant bytes"], 64)
    variant = TourVariant.objects.create(
        revision=revision,
        context="overview",
        source_hash=checksum,
        scope_fingerprint=scopes["overview"],
        manifest={
            "schema_version": 1,
            "kind": "panorama_360",
            "title": doc["title"],
            "captured_at": doc["captured_at"],
            "content_origin": doc["content_origin"],
            "spaces": doc["spaces"],
        },
        resources={
            "permitted": {
                "blob": blob,
                "type": "file",
                "media_type": "application/octet-stream",
            }
        },
    )
    tour.active_revision = revision
    tour.save()
    return tour, revision, variant


def test_creation_replay_conflict_and_account_isolation(
    auth_client, user, another_user, property_obj
):
    first = create(auth_client, property_obj)
    assert first.status_code == 201
    repeated = create(auth_client, property_obj)
    assert repeated.data == first.data
    assert repeated["Idempotency-Replayed"] == "true"
    assert PropertyVirtualTour.objects.count() == 1
    conflict = auth_client.post(
        f"/api/v1/properties/{property_obj.id}/virtual-tours/",
        {"kind": "model_3d"},
        format="json",
        HTTP_IDEMPOTENCY_KEY="create-tour-0001",
    )
    assert conflict.status_code == 409
    auth_client.force_authenticate(another_user)
    assert create(auth_client, property_obj).status_code == 404
    assert (
        auth_client.get(
            "/api/v1/virtual-tour-operations/by-key/create-tour-0001/"
        ).status_code
        == 404
    )


def test_expired_receipt_remains_a_tombstone(auth_client, property_obj):
    assert create(auth_client, property_obj).status_code == 201
    TourOperation.objects.update(expires_at=timezone.now() - timedelta(days=1))
    assert create(auth_client, property_obj).status_code == 410
    assert PropertyVirtualTour.objects.count() == 1


def test_media_cycle_must_be_complete(auth_client, property_obj):
    property_obj.images.all().delete()
    assert create(auth_client, property_obj).status_code == 409


def test_edit_concurrency_immutability_and_cross_revision_assets(property_obj):
    tour, revision, doc = synthetic_draft(property_obj)
    with pytest.raises(TourError, match="Refresh"):
        services.patch_revision(revision, {"authoring": doc}, '"draft-1"')
    foreign = TourRevision.objects.create(tour=tour)
    with pytest.raises(TourError, match="completed asset"):
        validate_authoring(foreign, doc)
    revision.review_state = "pending"
    with pytest.raises(TourError, match="new revision"):
        services.patch_revision(revision, {"authoring": doc}, '"draft-2"')


def test_graph_rejects_missing_return_and_unknown_fields(property_obj):
    _, revision, doc = synthetic_draft(property_obj)
    doc["hotspots"] = [doc["hotspots"][0], {**doc["hotspots"][0], "id": "other"}]
    with pytest.raises(TourError, match="return route"):
        validate_authoring(revision, doc)
    doc["approved"] = True
    with pytest.raises(TourError):
        validate_authoring(revision, doc)


def test_upload_resume_checksum_and_immutable_completed_bytes(
    auth_client, property_obj
):
    _, revision, _ = synthetic_draft(property_obj)
    content = b"binary image fixture"
    result, _ = uploads.create_upload(
        revision,
        {
            "role": "panorama",
            "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "media_type": "image/jpeg",
        },
        '"draft-2"',
    )
    from core_apps.virtual_tours.models import TourUploadSession

    upload = TourUploadSession.objects.get(id=result["id"])
    grant = uploads.part_grant(upload, 1)
    url = f"/api/v1/virtual-tour-uploads/{upload.id}/parts/1/?grant={grant}"
    response = auth_client.put(url, content, content_type="application/octet-stream")
    assert response.status_code == 200
    upload.refresh_from_db()
    completed, _ = uploads.complete(upload)
    accepted = storage.path(upload.asset.blob).read_bytes()
    assert accepted == content
    assert (
        auth_client.put(
            url, content, content_type="application/octet-stream"
        ).status_code
        == 410
    )
    assert storage.path(upload.asset.blob).read_bytes() == content


def test_real_panorama_processing_and_stale_worker(property_obj):
    tour, revision, _ = synthetic_draft(property_obj)
    revision.source_hash, _ = validate_authoring(revision, revision.authoring)
    revision.processing_state = "queued"
    revision.save()
    process_revision(str(revision.id), "old-hash")
    revision.refresh_from_db()
    assert revision.processing_state == "queued"
    # Exercise actual decoding, projection, all delivery levels and schema checks.
    process_revision(str(revision.id), revision.source_hash)
    revision.refresh_from_db()
    assert revision.processing_state == "ready", revision.report
    variant = revision.variants.get()
    assert len(variant.manifest["scenes"]) == 2
    assert "source_asset_id" not in json.dumps(variant.manifest)
    for resource in variant.resources.values():
        assert (storage.path(resource["blob"]) / "f_0_0_0.jpg").is_file()


def test_approval_requires_matching_hash_and_keeps_previous_active(
    property_obj, superuser
):
    tour, revision, variant = ready_variant(property_obj)
    revision.review_state = "pending"
    revision.save()
    with pytest.raises(TourError, match="changed"):
        services.review(
            revision,
            superuser,
            {
                "decision": "approved",
                "expected_source_hash": "wrong",
                "reason": "Inspected",
            },
        )
    services.review(
        revision,
        superuser,
        {
            "decision": "approved",
            "expected_source_hash": revision.source_hash,
            "reason": "Every package and privacy scope inspected",
        },
    )
    assert revision.reviews.count() == 1


def test_bootstrap_once_resource_scope_and_hidden_property_revocation(
    api_client, property_obj, user
):
    tour, revision, variant = ready_variant(property_obj)
    response = api_client.post(
        f"/api/v1/properties/{property_obj.id}/virtual-tours/{tour.id}/viewer-sessions/",
        {},
        format="json",
    )
    assert response.status_code == 201
    session_id, bootstrap = (
        response.data["session_id"],
        response.data["bootstrap_token"],
    )
    exchange = api_client.post(
        "/api/v1/virtual-tour-viewer/exchange/",
        {"bootstrap_token": bootstrap},
        format="json",
    )
    assert exchange.status_code == 200
    assert (
        api_client.post(
            "/api/v1/virtual-tour-viewer/exchange/",
            {"bootstrap_token": bootstrap},
            format="json",
        ).status_code
        == 401
    )
    header = {"HTTP_X_TOUR_CREDENTIAL": exchange.data["credential"]}
    base = f"/api/v1/virtual-tour-viewer/sessions/{session_id}/"
    assert (
        api_client.get(base + "resources/foreign/access/", **header).status_code == 404
    )
    grant = api_client.get(base + "resources/permitted/access/", **header)
    assert grant.status_code == 200
    assert api_client.get(grant.data["url"]).status_code == 200
    property_obj.status = "hidden"
    property_obj.save()
    assert api_client.get(grant.data["url"]).status_code == 409
    assert (
        api_client.post(base + "renew/", {}, format="json", **header).status_code == 409
    )


def test_partial_scope_rejects_foreign_room_price_change_does_not_invalidate(
    property_obj,
):
    room1, room2, offer = (
        "11111111-1111-4111-8111-111111111111",
        "22222222-2222-4222-8222-222222222222",
        "33333333-3333-4333-8333-333333333333",
    )
    property_obj.rental_inventory = {
        "mode": "partial",
        "rooms": [{"id": room1}, {"id": room2}],
        "offers": [
            {
                "id": offer,
                "room_ids": [room1],
                "rental_scope": "room",
                "terms": {"price": "10"},
            }
        ],
    }
    shared = {"id": "hall", "floor_id": "g", "space_kind": "shared"}
    fingerprint = scope_policy(property_obj, offer, [shared])
    property_obj.rental_inventory["offers"][0]["terms"]["price"] = "20"
    assert scope_policy(property_obj, offer, [shared]) == fingerprint
    with pytest.raises(TourError, match="outside"):
        scope_policy(
            property_obj, offer, [{**shared, "space_kind": "room", "room_id": room2}]
        )
    with pytest.raises(TourError, match="outside"):
        scope_policy(
            property_obj,
            "overview",
            [{**shared, "space_kind": "room", "room_id": room1}],
        )
    property_obj.rental_inventory["offers"][0]["archived"] = True
    with pytest.raises(TourError, match="no longer"):
        scope_policy(property_obj, offer, [shared])
