"""Reviewed response versions, durable replay and absence fencing."""

# flake8: noqa: F401,F811 -- pytest fixtures injected by name.
import uuid
import pytest
from core_apps.features.tests.test_rental_phase2 import (
    rental_participants,
    authenticated,
)
from core_apps.features.tests.test_cycle_concurrency import parallel_calls
from core_apps.features.models import IdempotencyRecord
from core_apps.features.planning_models import PlanningEvent
from core_apps.properties.models import PropertyVisit
from .test_viewing_event_history import request_visit

pytestmark = pytest.mark.django_db
API = "/api/v1/properties/"


def send(user, visit, action, key=None, revision=None):
    return authenticated(user).post(
        API + f"visits/{visit.id}/commands/",
        {
            "request_key": key or str(uuid.uuid4()),
            "expected_revision": revision or visit.revision,
            "action": action,
        },
        format="json",
    )


def test_stale_response_is_rejected_and_original_request_recovers_current_state(
    rental_participants,
):
    owner, tenant, _, _, _ = rental_participants
    visit = request_visit(rental_participants)
    key = str(uuid.uuid4())
    first = send(owner, visit, "accept", key)
    assert first.status_code == 200, first.data
    second = send(owner, visit, "accept", key)
    assert second.status_code == 200 and second.data == first.data
    assert send(owner, visit, "reject").status_code == 409
    assert send(owner, visit, "reject", key).status_code == 409
    visit.refresh_from_db()
    assert send(tenant, visit, "cancel").status_code == 200
    receipt = authenticated(owner).post(
        API + f"visits/{visit.id}/commands/resolve/",
        {"request_key": key},
        format="json",
    )
    assert receipt.status_code == 200
    assert receipt.data["action"] == "accept" and receipt.data["status"] == "confirmed"
    assert receipt.data["visit"]["status"] == "canceled"
    visit.refresh_from_db()
    assert visit.revision == 3


@pytest.mark.parametrize(
    "endpoint,method,body",
    [
        ("owner/visits/requests/{id}/accept/", "post", {}),
        ("owner/visits/requests/{id}/reject/", "post", {"reason": "visit_unavailable"}),
        ("visits/{id}/cancel/", "post", {}),
        ("visits/{id}/update/", "patch", {"status": "canceled"}),
    ],
)
def test_existing_entry_points_require_the_reviewed_revision(
    rental_participants, endpoint, method, body
):
    owner, tenant, _, _, _ = rental_participants
    visit = request_visit(rental_participants)
    user = owner if endpoint.startswith("owner") else tenant
    path = API + endpoint.format(id=visit.id)
    response = getattr(authenticated(user), method)(path, body, format="json")
    assert response.status_code == 400, (path, response.data)
    visit.refresh_from_db()
    assert visit.status == "pending" and visit.revision == 1


def test_absence_is_fenced_and_delayed_request_cannot_execute(rental_participants):
    owner, _, _, _, _ = rental_participants
    visit = request_visit(rental_participants)
    key = str(uuid.uuid4())
    response = authenticated(owner).post(
        API + f"visits/{visit.id}/commands/resolve/",
        {"request_key": key},
        format="json",
    )
    assert response.status_code == 200 and response.data["status"] == "absent_final"
    assert send(owner, visit, "accept", key).status_code == 409
    visit.refresh_from_db()
    assert visit.status == "pending"


def test_other_party_cannot_use_owner_response_and_missing_key_is_invalid(
    rental_participants,
):
    owner, tenant, outsider, _, _ = rental_participants
    visit = request_visit(rental_participants)
    assert send(tenant, visit, "accept").status_code == 403
    assert send(outsider, visit, "accept").status_code == 404
    assert (
        authenticated(owner)
        .post(
            API + f"visits/{visit.id}/commands/",
            {"expected_revision": 1, "action": "accept"},
            format="json",
        )
        .status_code
        == 400
    )


@pytest.mark.django_db(transaction=True)
def test_owner_response_and_tenant_cancel_are_serialized(rental_participants):
    owner, tenant, _, _, _ = rental_participants
    visit = request_visit(rental_participants)
    responses = parallel_calls(
        lambda i: send(
            owner if i == 0 else tenant, visit, "accept" if i == 0 else "cancel"
        )
    )
    assert sorted(r.status_code for r in responses) == [200, 409]
    visit.refresh_from_db()
    assert visit.revision == 2 and len(visit.change_history) == 2
    assert (
        IdempotencyRecord.objects.filter(
            operation=f"viewing.command:{visit.id}"
        ).count()
        == 1
    )


@pytest.mark.django_db(transaction=True)
def test_same_response_from_two_devices_runs_once(rental_participants):
    owner, _, _, _, _ = rental_participants
    visit = request_visit(rental_participants)
    key = str(uuid.uuid4())
    responses = parallel_calls(lambda _: send(owner, visit, "accept", key))
    assert [r.status_code for r in responses] == [200, 200]
    assert responses[0].data == responses[1].data
    visit.refresh_from_db()
    assert visit.revision == 2
    assert (
        PlanningEvent.objects.filter(
            destination__visit_id=str(visit.id), destination__change="accepted"
        ).count()
        == 2
    )
