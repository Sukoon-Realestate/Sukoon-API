"""Run with config.settings.postgres_test; SQLite cannot prove row-lock behavior."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import copy
import uuid
import pytest
from django.db import connection, connections, close_old_connections
from .test_shared_housing import pair, create, candidate, proposal_act, API
from .test_rental_phase2 import rental_participants, authenticated
from .test_funded_settlement import command
from core_apps.features.shared_housing_models import SharedHousingPlan
from core_apps.features.models import RentalInterest

pytestmark = pytest.mark.django_db(transaction=True)


def race(calls):
    if connection.vendor != "postgresql":
        pytest.skip("Requires real PostgreSQL row locking")
    barrier = Barrier(len(calls))

    def execute(call):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return call()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        return list(pool.map(execute, calls))


def test_crossed_creation_returns_one_plan(pair):
    _, first, second, _, _ = pair
    # Obtain a valid command without retaining a plan.
    plan, body = create(pair)
    SharedHousingPlan.objects.filter(id=plan["id"]).update(status="closed")
    bodies = [
        {**copy.deepcopy(body), "request_key": str(uuid.uuid4())} for _ in range(2)
    ]
    results = race(
        [
            lambda: authenticated(first).post(
                API + "shared-housing-plans/", bodies[0], format="json"
            ),
            lambda: authenticated(second).post(
                API + "shared-housing-plans/", bodies[1], format="json"
            ),
        ]
    )
    assert [r.status_code for r in results] == [201, 201]
    assert results[0].data["resource"]["id"] == results[1].data["resource"]["id"]
    assert SharedHousingPlan.objects.exclude(status="closed").count() == 1


def test_submission_and_withdrawal_never_leave_one_interest(pair):
    _, first, second, _, _ = pair
    plan = candidate(pair)
    for user in [first, second]:
        plan = proposal_act(user, plan, "consent_selection", consent=True)
    base = API + f"shared-housing-plans/{plan['id']}/"
    results = race(
        [
            lambda: authenticated(first).post(
                base + f"proposals/{plan['proposals'][0]['id']}/submit/",
                command(plan["revision"]),
                format="json",
            ),
            lambda: authenticated(second).post(
                base + "withdraw/", command(plan["revision"]), format="json"
            ),
        ]
    )
    assert sorted(r.status_code for r in results) == [200, 409]
    result = SharedHousingPlan.objects.get(id=plan["id"])
    assert (result.status, RentalInterest.objects.count()) in {
        ("closed", 0),
        ("reviewing", 2),
    }
