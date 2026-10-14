import uuid

import pytest

from core_apps.features.models import MaintenanceRequest, MaintenanceEvent
from core_apps.features.tests.test_rental_phase5 import phase5_lease, client_for

pytestmark = pytest.mark.django_db


def test_proposed_cost_validates_money_units_and_legacy_defaults(phase5_lease):
    owner, tenant, lease = phase5_lease
    item = MaintenanceRequest.objects.create(
        lease=lease,
        reporter=tenant,
        title="Repair",
        description="Local repair",
        category="plumbing",
        priority="normal",
    )
    client = client_for(owner)
    path = f"/api/v1/features/v1/maintenance-requests/{item.id}/actions/"
    body = {
        "action": "propose_cost",
        "note": "Estimate",
        "cost_payer": "tenant",
        "expected_revision": item.revision,
        "request_key": str(uuid.uuid4()),
    }
    for cost in (
        None,
        [],
        {},
        {"amount_minor": None},
        {"amount_minor": True},
        {"amount_minor": 1.5},
        {"amount_minor": 0},
        {"amount_minor": -1},
        {"amount_minor": 10**12 + 1},
        {"amount_minor": 2500, "currency": "USD", "exponent": 2},
        {"amount_minor": 2500, "currency": "EGP", "exponent": 3},
        {"amount_minor": 2500, "currency": None, "exponent": 2},
        {"amount_minor": 2500, "currency": "EGP", "exponent": None},
    ):
        denied = client.post(path, {**body, "cost": cost}, format="json")
        assert denied.status_code == 400 and denied.json()["data"] is None
    item.refresh_from_db()
    assert item.revision == 1 and item.cost_version == 0
    assert not MaintenanceEvent.objects.filter(maintenance_request=item).exists()
    # Existing clients may omit the fixed denomination; default EGP/2 remains.
    legacy = {**body, "cost": {"amount_minor": 2500}}
    accepted = client.post(path, legacy, format="json")
    assert accepted.status_code == 200
    assert accepted.json()["data"]["resource"]["proposed_cost"] == {
        "amount_minor": 2500,
        "currency": "EGP",
        "exponent": 2,
    }
    assert client.post(path, legacy, format="json").json() == accepted.json()


def test_exact_cost_version_validation_replay_and_authorization(phase5_lease):
    owner, tenant, lease = phase5_lease
    item = MaintenanceRequest.objects.create(
        lease=lease,
        reporter=tenant,
        title="Repair",
        description="Local repair",
        category="plumbing",
        priority="normal",
        cost_payer="tenant",
        status="appointment_proposed",
        proposed_cost_minor=2500,
        cost_version=3,
    )
    path = f"/api/v1/features/v1/maintenance-requests/{item.id}/"
    client = client_for(tenant)
    current = client.get(path).json()["data"]
    assert current["status"] == "appointment_proposed"
    assert current["cost_version"] == 3
    assert current["approved_cost_version"] is None
    assert "approve_cost" in current["allowed_actions"]
    body = {
        "action": "approve_cost",
        "note": "Reviewed this estimate",
        "cost_version": 3,
        "expected_revision": 1,
        "request_key": str(uuid.uuid4()),
    }
    command = path + "actions/"
    missing = {key: value for key, value in body.items() if key != "cost_version"}
    for malformed in [
        missing,
        *({**body, "cost_version": value} for value in (None, "", True, 0)),
    ]:
        response = client.post(command, malformed, format="json")
        assert response.status_code == 400 and response.json()["data"] is None
    assert client_for(owner).post(command, body, format="json").status_code == 403
    assert (
        client.post(command, {**body, "cost_version": 2}, format="json").status_code
        == 409
    )
    assert (
        client.post(
            command, {**body, "expected_revision": 99}, format="json"
        ).status_code
        == 409
    )
    stranger = type(tenant).objects.create_user(
        email="maintenance-stranger@example.com", password="pass"
    )
    assert client_for(stranger).post(command, body, format="json").status_code == 404
    first = client.post(command, body, format="json")
    replay = client.post(command, body, format="json")
    assert first.status_code == replay.status_code == 200
    assert first.json() == replay.json()
    value = first.json()["data"]["resource"]
    assert value["cost_version"] == value["approved_cost_version"] == 3
    assert value["revision"] == 2
    assert "approve_cost" not in value["allowed_actions"]
    assert MaintenanceEvent.objects.filter(maintenance_request=item).count() == 1
    assert (
        client.post(
            command,
            {**body, "expected_revision": 2, "request_key": str(uuid.uuid4())},
            format="json",
        ).status_code
        == 409
    )


def test_legacy_action_extras_keep_their_existing_replay_identity(phase5_lease):
    owner, tenant, lease = phase5_lease
    item = MaintenanceRequest.objects.create(
        lease=lease,
        reporter=tenant,
        title="Repair",
        description="Local repair",
        category="plumbing",
        priority="normal",
    )
    body = {
        "action": "reply",
        "note": "Available tomorrow",
        "appointment_at": "",
        "cost": {"amount_minor": None, "currency": "", "exponent": 2},
        "cost_payer": "",
        "evidence_ids": [],
        "expected_revision": 1,
        "request_key": str(uuid.uuid4()),
    }
    client = client_for(tenant)
    path = f"/api/v1/features/v1/maintenance-requests/{item.id}/actions/"
    first = client.post(path, body, format="json")
    assert first.status_code == 200
    assert client.post(path, body, format="json").json() == first.json()
    compact = {
        k: v
        for k, v in body.items()
        if k not in {"appointment_at", "cost", "cost_payer", "evidence_ids"}
    }
    assert client.post(path, compact, format="json").status_code == 409


@pytest.mark.parametrize("value", [[], ["morning", "after 18:00"], "", "after 18:00"])
def test_access_times_array_and_legacy_string_keep_replay(phase5_lease, value):
    _, tenant, lease = phase5_lease
    client = client_for(tenant)
    path = f"/api/v1/features/v1/leases/{lease.id}/maintenance-requests/"
    body = {
        "title": "Repair",
        "description": "Pipe",
        "category": "plumbing",
        "priority": "normal",
        "access_times": value,
        "evidence_ids": [],
        "expected_revision": 0,
        "request_key": str(uuid.uuid4()),
    }
    first = client.post(path, body, format="json")
    assert first.status_code == 201
    assert first.json()["data"]["resource"]["access_times"] == value
    assert client.post(path, body, format="json").json() == first.json()


@pytest.mark.parametrize(
    "extra", [{}, {"access_times": None}, {"access_times": {}}, {"access_times": [1]}]
)
def test_missing_null_or_nontext_access_times_are_not_stored(phase5_lease, extra):
    _, tenant, lease = phase5_lease
    response = client_for(tenant).post(
        f"/api/v1/features/v1/leases/{lease.id}/maintenance-requests/",
        {
            "title": "Repair",
            "description": "Pipe",
            "category": "plumbing",
            "priority": "normal",
            "evidence_ids": [],
            "expected_revision": 0,
            "request_key": str(uuid.uuid4()),
            **extra,
        },
        format="json",
    )
    assert response.status_code == 400 and response.json()["data"] is None
    assert not MaintenanceRequest.objects.filter(lease=lease).exists()
