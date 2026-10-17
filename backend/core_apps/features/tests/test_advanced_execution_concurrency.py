"""PostgreSQL proves competing plans cannot reserve the same physical offer."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connection

from core_apps.features.models import Lease, RentalInventoryDayLock
from .test_advanced_execution import (
    API,
    act,
    authenticated,
    command,
    enabled,
    execution_enabled,
    post,
    ready,
    rental_participants,
)
from . import test_advanced_execution as test_advanced_execution_fixtures

scenario = test_advanced_execution_fixtures.scenario


@pytest.mark.django_db(transaction=True)
def test_competing_execution_plans_preserve_one_canonical_reservation(scenario):
    if connection.vendor != "postgresql":
        pytest.skip("Competing physical inventory reservations require PostgreSQL")
    first = ready(scenario, prepare=False)
    package = authenticated(scenario[1]).get(
        API + f"housing-packages/{first['source_id']}/"
    )
    assert package.status_code == 200, package.data
    second = post(
        scenario[1],
        f"housing-packages/{first['source_id']}/prepare/",
        command(
            package.data["revision"],
            digest=package.data["digest"],
            execution_mode="conditional_package",
        ),
    )["resource"]
    for actor in scenario[:2]:
        second = act(
            actor,
            second,
            "consents",
            decision="accept",
            policy_version=second["policy_version"],
        )
    assert first["id"] != second["id"]
    barrier = Barrier(2)

    def prepare(pair):
        actor, plan = pair
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            response = authenticated(actor).post(
                API + f"advanced-executions/{plan['id']}/prepare/",
                command(plan["revision"], digest=plan["digest"]),
                format="json",
            )
            return response.status_code, response.data
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(prepare, [(scenario[0], first), (scenario[1], second)]))
    assert sorted(status for status, _ in results) == [200, 409], results
    assert Lease.objects.count() == 1
    assert RentalInventoryDayLock.objects.values("lease_id").distinct().count() == 1
    assert not Lease.objects.get().signing_sessions.exists()
