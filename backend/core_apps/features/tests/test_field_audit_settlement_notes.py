import uuid

import pytest

from core_apps.features.models import FinalSettlement
from core_apps.features.tests.test_rental_phase6 import phase6_lease, client_for

pytestmark = pytest.mark.django_db


def test_settlement_notes_persist_across_revisions_without_rewriting_money(
    phase6_lease,
):
    owner, tenant, lease = phase6_lease
    owner_client, tenant_client = client_for(owner), client_for(tenant)
    path = f"/api/v1/features/v1/leases/{lease.id}/final-settlement/"
    initial = owner_client.get(path).json()["data"]
    assert initial["notes"] == []
    body = {
        "expected_revision": initial["revision"],
        "request_key": str(uuid.uuid4()),
        "lines": [],
        "note": "No outstanding deductions",
    }
    for value in (None, [], 12, "x" * 4001):
        denied = owner_client.post(
            path + "propose/", {**body, "note": value}, format="json"
        )
        assert denied.status_code == 400 and denied.json()["data"] is None
    first = owner_client.post(path + "propose/", body, format="json")
    assert first.status_code == 200
    assert (
        owner_client.post(path + "propose/", body, format="json").json() == first.json()
    )
    proposal = first.json()["data"]["resource"]
    assert proposal["notes"][0]["note"] == body["note"]
    assert proposal["notes"][0]["revision"] == proposal["revision"]
    assert proposal["notes"][0]["actor_role"] == "owner"
    assert "actor_id" not in proposal["notes"][0]
    assert proposal["notes"][0]["id"] == body["request_key"]
    assert (
        owner_client.post(
            path + "propose/", {**body, "note": "changed"}, format="json"
        ).status_code
        == 409
    )
    reply = {
        "decision": "accept",
        "note": "Agreed after checking the statement",
        "expected_revision": proposal["revision"],
        "request_key": str(uuid.uuid4()),
    }
    accepted = tenant_client.post(path + "respond/", reply, format="json")
    assert accepted.status_code == 200
    assert (
        tenant_client.post(path + "respond/", reply, format="json").json()
        == accepted.json()
    )
    final = owner_client.get(path).json()["data"]
    assert [n["note"] for n in final["notes"]] == [body["note"], reply["note"]]
    assert [n["action"] for n in final["notes"]] == ["propose", "accept"]
    assert final["notes"][1]["actor_role"] == "tenant"
    assert final["lines"] == proposal["lines"] == []
    for field in ("rent_balance", "deposit_to_return", "refund_due", "total_due"):
        assert final[field] == proposal[field]
    saved = FinalSettlement.objects.get(lease=lease)
    assert len(saved.history) == 1
    assert saved.history[0]["notes"][0]["actor_id"] == str(owner.id)
    assert final["history"] == [
        {key: value for key, value in entry.items() if key != "notes"}
        for entry in saved.history
    ]
    assert all("notes" not in entry for entry in proposal["history"])
    outsider = type(owner).objects.create_user(
        email="settlement-outsider@example.com", password="pass"
    )
    assert client_for(outsider).get(path).status_code == 404


@pytest.mark.parametrize("extra", [{}, {"note": ""}, {"note": "   "}])
def test_missing_or_empty_note_does_not_fabricate_history_comment(phase6_lease, extra):
    owner, _, lease = phase6_lease
    client = client_for(owner)
    path = f"/api/v1/features/v1/leases/{lease.id}/final-settlement/"
    revision = client.get(path).json()["data"]["revision"]
    response = client.post(
        path + "propose/",
        {
            "lines": [],
            "expected_revision": revision,
            "request_key": str(uuid.uuid4()),
            **extra,
        },
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["data"]["resource"]["notes"] == []
