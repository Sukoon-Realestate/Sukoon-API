"""Synthetic interior fixtures; these are not scans of a real property."""

import copy
import json
import struct
import uuid
from pathlib import Path
from datetime import timedelta
import pytest
from django.utils import timezone
from core_apps.virtual_tours import services, sessions, storage
from core_apps.virtual_tours.errors import TourError
from core_apps.virtual_tours.models import (
    PropertyVirtualTour,
    TourRevision,
    TourAsset,
    TourViewerSession,
)
from core_apps.virtual_tours.policy import enabled, scope_policy
from core_apps.virtual_tours.processing import process_revision
from core_apps.virtual_tours.validation import (
    validate_authoring,
    validate_glb,
    validate_spawns,
)
from .test_tours import ready_variant, synthetic_draft

pytestmark = pytest.mark.django_db


def floor_glb(external=False, scale=False):
    # Two counter-clockwise triangles form an 8m square floor facing +Y.
    positions = [-4, 0, -4, 4, 0, -4, 4, 0, 4, -4, 0, 4]
    indices = [0, 2, 1, 0, 3, 2]
    data = struct.pack("<12f6H", *positions, *indices)
    doc = {
        "asset": {"version": "2.0", "generator": "Sokoun synthetic calibration test"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "buffers": [{"byteLength": len(data)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 48, "target": 34962},
            {"buffer": 0, "byteOffset": 48, "byteLength": 12, "target": 34963},
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": 4,
                "type": "VEC3",
                "min": [-4, 0, -4],
                "max": [4, 0, 4],
            },
            {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"},
        ],
    }
    if external:
        doc["buffers"][0]["uri"] = "https://external.invalid/private.bin"
    if scale:
        doc["nodes"][0]["scale"] = [1, 2, 1]
    encoded = json.dumps(doc, separators=(",", ":")).encode()
    encoded += b" " * (-len(encoded) % 4)
    return (
        struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(encoded) + 8 + len(data))
        + struct.pack("<II", len(encoded), 0x4E4F534A)
        + encoded
        + struct.pack("<II", len(data), 0x004E4942)
        + data
    )


def asset(revision, role, content):
    key, size, checksum = storage.write_blob([content], len(content))
    return TourAsset.objects.create(
        revision=revision,
        role=role,
        blob=key,
        size=size,
        sha256=checksum,
        media_type="application/json" if role == "walk" else "model/gltf-binary",
    )


@pytest.fixture
def model_revision(property_obj, settings):
    scripts = Path(__file__).resolve().parents[3] / "tools" / "virtual_tours"
    settings.VIRTUAL_TOUR_GLTF_VALIDATOR = str(scripts / "validate-glb.cjs")
    settings.VIRTUAL_TOUR_SPAWN_VALIDATOR = str(scripts / "validate-spawns.mjs")
    tour = PropertyVirtualTour.objects.create(property=property_obj, kind="model_3d")
    revision = TourRevision.objects.create(tour=tour)
    visual = asset(revision, "visual", floor_glb())
    collider = asset(revision, "collision", floor_glb())
    walk = asset(
        revision,
        "walk",
        json.dumps(
            {
                "schema_version": 1,
                "regions": [
                    {
                        "id": "hall",
                        "space_id": "hall",
                        "floor_id": "g",
                        "floor_y": 0,
                        "polygon_xz": [[-4, -4], [4, -4], [4, 4], [-4, 4]],
                    }
                ],
            }
        ).encode(),
    )
    label = {"ar": "اختبار اصطناعي", "en": "Synthetic calibration floor"}
    doc = {
        "schema_version": 1,
        "kind": "model_3d",
        "title": label,
        "captured_at": "2026-01-01",
        "content_origin": "representative_model",
        "coordinate_system": "right_handed_y_up_meters",
        "spaces": [
            {"id": "hall", "floor_id": "g", "space_kind": "shared", "label": label}
        ],
        "variants": [
            {
                "context": "overview",
                "space_ids": ["hall"],
                "visual_asset_id": str(visual.id),
                "collision_asset_id": str(collider.id),
                "walk_asset_id": str(walk.id),
                "start_spawn_id": "start",
                "spawns": [
                    {
                        "id": "start",
                        "space_id": "hall",
                        "floor_id": "g",
                        "foot_position_m": [0, 0, 0],
                        "yaw_rad": 0,
                        "pitch_rad": 0,
                    }
                ],
            }
        ],
    }
    services.patch_revision(revision, {"authoring": doc}, '"draft-1"')
    return revision, collider


def test_real_khronos_and_rapier_processing(model_revision):
    revision, collider = model_revision
    revision.source_hash, _ = validate_authoring(revision, revision.authoring)
    revision.processing_state = "queued"
    revision.save()
    process_revision(str(revision.id), revision.source_hash)
    revision.refresh_from_db()
    assert revision.processing_state == "ready", revision.report
    variant = revision.variants.get()
    assert variant.manifest["movement"]["capsule_height_m"] == 1.75
    assert variant.manifest["interaction"]["free_fly"] is False
    assert len(variant.resources) == 3
    assert not any(
        k in json.dumps(variant.manifest)
        for k in ["source_asset_id", "blob", "private_virtual_tours"]
    )


def test_model_external_uris_scale_and_ungrounded_spawn_are_rejected(model_revision):
    revision, collider = model_revision
    with pytest.raises(TourError, match="embedded"):
        validate_glb(asset(revision, "visual", floor_glb(external=True)))
    with pytest.raises(TourError, match="Bake scale"):
        validate_glb(asset(revision, "visual", floor_glb(scale=True)))
    variant = copy.deepcopy(revision.authoring["variants"][0])
    variant["spawns"][0]["foot_position_m"][1] = 2
    with pytest.raises(TourError, match="safe ground"):
        validate_spawns(collider, variant)


def test_model_preparation_capability_requires_real_worker_validators(settings):
    settings.VIRTUAL_TOUR_GLTF_VALIDATOR = ""
    settings.VIRTUAL_TOUR_SPAWN_VALIDATOR = ""
    assert not enabled("model_3d", True)
    assert enabled("panorama_360", True)


def test_adding_a_bed_invalidates_room_package_but_price_does_not(property_obj):
    room, offer = str(uuid.uuid4()), str(uuid.uuid4())
    property_obj.rental_inventory = {
        "mode": "partial",
        "rooms": [{"id": room, "beds": []}],
        "offers": [{"id": offer, "rental_scope": "room", "room_ids": [room]}],
    }
    spaces = [{"id": "bedroom", "floor_id": "g", "space_kind": "room", "room_id": room}]
    before = scope_policy(property_obj, offer, spaces)
    property_obj.rental_inventory["rooms"][0]["beds"].append({"id": str(uuid.uuid4())})
    assert scope_policy(property_obj, offer, spaces) != before


def test_unpublish_revokes_existing_credentials_and_preview_is_owner_only(
    api_client, property_obj, user, another_user
):
    tour, revision, variant = ready_variant(property_obj)
    with pytest.raises(TourError, match="restricted"):
        sessions.create_session(
            tour, another_user, {"preview": True, "revision_id": str(revision.id)}
        )
    result = sessions.create_session(tour, user, {})
    session = TourViewerSession.objects.select_related(
        "variant__revision__tour__property", "user"
    ).get(id=result["session_id"])
    credential = sessions.exchange(session)["credential"]
    tour.disabled = True
    tour.save()
    session = TourViewerSession.objects.select_related(
        "variant__revision__tour__property", "user"
    ).get(id=result["session_id"])
    with pytest.raises(TourError, match="no longer published"):
        sessions.authenticate_session(session, credential)


def test_reviewer_console_requires_staff_and_hash_bound_decision(
    api_client, property_obj, user, superuser, settings
):
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    tour, revision, variant = ready_variant(property_obj)
    revision.review_state = "pending"
    revision.save()
    url = f"/admin/virtual_tours/tourrevision/{revision.pk}/review/"
    assert api_client.get(url).status_code == 302
    api_client.force_login(superuser)
    assert api_client.get(url).status_code == 200
    response = api_client.post(
        url, {"decision": "approved", "source_hash": "wrong", "reason": "Reviewed"}
    )
    assert response.status_code == 200
    revision.refresh_from_db()
    assert revision.review_state == "pending"
    response = api_client.post(
        url,
        {
            "decision": "approved",
            "source_hash": revision.source_hash,
            "reason": "Inspected all downloadable packages and private areas",
        },
    )
    assert response.status_code == 302
    revision.refresh_from_db()
    assert revision.review_state == "approved"
