import uuid

import pytest

from core_apps.features.models import RentalChange, RentalHandover, RentalTimelineEvent
from core_apps.features.tests.test_rental_phase5 import phase5_lease, client_for

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("kind", ["handover", "change"])
def test_response_explanation_reaches_private_timeline_once(phase5_lease, kind):
    owner, tenant, lease = phase5_lease
    if kind == "handover":
        item = RentalHandover.objects.create(
            lease=lease,
            kind="move_in",
            possession_on=lease.start_date,
            status="pending_approval",
            condition={},
            keys={},
            meters={},
            inventory=[],
        )
        path = f"handovers/{item.id}/respond/"
        action = "dispute"
    else:
        item = RentalChange.objects.create(
            lease=lease, requester=owner, kind="amendment"
        )
        path = f"amendments/{item.id}/respond/"
        action = "request_changes"
    url = "/api/v1/features/v1/" + path
    client = client_for(tenant)
    body = {
        "decision": action,
        "note": "Please correct the recorded condition",
        "expected_revision": item.revision,
        "request_key": str(uuid.uuid4()),
    }
    for value in (None, [], 9, "x" * 4001):
        invalid = client.post(url, {**body, "note": value}, format="json")
        assert invalid.status_code == 400 and invalid.json()["data"] is None
    first = client.post(url, body, format="json")
    assert first.status_code == 200
    assert client.post(url, body, format="json").json() == first.json()
    assert (
        client.post(url, {**body, "note": "changed"}, format="json").status_code == 409
    )
    assert (
        client.post(
            url, {**body, "request_key": str(uuid.uuid4())}, format="json"
        ).status_code
        == 409
    )
    event = RentalTimelineEvent.objects.get(lease=lease, resource_id=item.id)
    assert event.actor == tenant and event.description == body["note"]
    timeline = f"/api/v1/features/v1/leases/{lease.id}/timeline/"
    for participant in (owner, tenant):
        response = client_for(participant).get(timeline, HTTP_ACCEPT_LANGUAGE="ar")
        assert response.status_code == 200
        row = next(r for r in response.json()["data"] if r["id"] == str(event.id))
        assert row["description"] == body["note"]
        assert row["resource_id"] == str(item.id)
        assert row["label"] in ("محضر التسليم: اعتراض", "طلب تعديل العقد: طلب تعديلات")
    outsider = type(owner).objects.create_user(
        email="response-outsider@example.com", password="pass"
    )
    assert client_for(outsider).get(timeline).status_code == 404
    assert client_for(outsider).post(url, body, format="json").status_code == 404


@pytest.mark.parametrize("note", ["", "   "])
def test_empty_response_note_does_not_create_a_timeline_entry(phase5_lease, note):
    owner, tenant, lease = phase5_lease
    item = RentalChange.objects.create(lease=lease, requester=owner, kind="amendment")
    response = client_for(tenant).post(
        f"/api/v1/features/v1/amendments/{item.id}/respond/",
        {
            "decision": "reject",
            "note": note,
            "expected_revision": 1,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert response.status_code == 200
    assert not RentalTimelineEvent.objects.filter(resource_id=item.id).exists()
