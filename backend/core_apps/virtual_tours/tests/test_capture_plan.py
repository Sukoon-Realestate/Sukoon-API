import copy
import json
import os
from pathlib import Path
import pytest
from core_apps.virtual_tours.capture_validation import MODES, POLICY, CONVENTION
from core_apps.virtual_tours.models import PropertyVirtualTour
from .test_capture import capture, upload, uid

pytestmark = pytest.mark.django_db


def document(capture, meta):
    session, _, room, _ = capture
    return {"schemaVersion": 1, "sessionId": str(session.id), "propertyId": str(session.property.id),
        "requestedOutputs": list(MODES), "capturePolicyVersion": POLICY, "coordinateConvention": CONVENTION,
        "roomIds": [room], "frameIds": [meta["frameId"]],
        "coveragePlan": {"schemaVersion": 1, "revision": 1,
            "rooms": [{"id": room, "label": "Fixture bedroom", "ownerStatus": "complete", "revision": 1}],
            "stations": [{"id": uid(), "roomId": room, "label": "Door station", "ownerStatus": "complete", "revision": 1,
                "nativeStationIds": [meta["stationId"]]}]}}


def test_private_plan_manifest_uses_existing_upload_receipt_and_never_publishes(capture, auth_client, another_user):
    session, base, room, post = capture
    meta, _, _ = upload(capture, auth_client, "panorama360")
    doc = document(capture, meta)
    key = uid()
    body = {"expectedRevision": session.revision, "document": doc}
    result = post(base + "manifests/", body, key)
    assert result.status_code == 201, result.data
    assert post(base + "manifests/", body, key).data == result.data
    current = auth_client.get("/api/v1/" + base)
    assert current.status_code == 200 and current.data["coveragePlan"] == doc["coveragePlan"]
    assert not PropertyVirtualTour.objects.exists()
    exported = os.environ.get("MVP_FIXTURE_DIR")
    if exported:
        (Path(exported) / "capture_coverage_plan.json").write_text(json.dumps(doc["coveragePlan"]), encoding="utf8")
    auth_client.force_authenticate(another_user)
    assert auth_client.get("/api/v1/" + base).status_code == 404
    assert post(base + "manifests/", body).status_code == 404


@pytest.mark.parametrize("fault", ["cross_room", "duplicate_station", "no_evidence", "invalid_state", "invalid_attempt", "invalid_room_type"])
def test_plan_cannot_relabel_physical_capture_or_claim_missing_evidence(capture, auth_client, fault):
    session, base, room, post = capture
    meta, _, _ = upload(capture, auth_client, "panorama360")
    doc = document(capture, meta); plan = doc["coveragePlan"]
    station = plan["stations"][0]
    if fault == "cross_room":
        other = uid(); assert post(base + "rooms/", {"id": other, "label": "Other room", "confirmed": True}).status_code == 200
        plan["rooms"].append({"id": other, "label": "Other room", "ownerStatus": "incomplete", "revision": 1})
        station["roomId"] = other
    elif fault == "duplicate_station":
        second = copy.deepcopy(station); second["id"] = uid(); plan["stations"].append(second)
    elif fault == "no_evidence": station["nativeStationIds"] = []
    elif fault == "invalid_state": station["ownerStatus"] = ["complete"]
    elif fault == "invalid_attempt": station["nativeStationIds"] = [[uid()]]
    else: station["roomId"] = [room]
    result = post(base + "manifests/", {"expectedRevision": session.revision, "document": doc})
    assert result.status_code == 422, result.data
