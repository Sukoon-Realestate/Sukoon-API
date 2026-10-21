"""Core company interleavings on real PostgreSQL, without provider execution."""

import pytest
from django.db import connection

from core_apps.features.company_models import CompanyBudgetReservation
from core_apps.features.models import Lease, PaymentAttempt, RentalInventoryDayLock
from core_apps.features.services.company import bookings
from core_apps.features.services.rental_phase2 import RentalConflict
from .test_company_contract_preparation import (
    API,
    authenticated,
    command,
    create,
    cycle,
    respond,
)
from .test_company_housing import company_setup, policy, proposed, rental_participants
from .test_cycle_concurrency import parallel_calls


def require_postgres():
    if connection.vendor != "postgresql":
        pytest.skip("This assertion requires PostgreSQL transaction locks.")


@pytest.mark.django_db(transaction=True)
def test_approval_and_withdrawal_cannot_both_commit_same_revision(company_setup):
    require_postgres()
    item = proposed(company_setup)
    revision, digest = item.revision, item.snapshot_digest

    def act(index):
        try:
            if index == 0:
                bookings.decide(
                    company_setup[2],
                    item.id,
                    {
                        "expected_revision": revision,
                        "snapshot_digest": digest,
                        "decision": "approved",
                    },
                )
                return "approved"
            bookings.withdraw_item(
                company_setup[1], item.id, {"expected_revision": revision}
            )
            return "withdrawn"
        except RentalConflict:
            return "conflict"

    outcomes = parallel_calls(act)
    assert outcomes.count("conflict") == 1
    item.refresh_from_db()
    winner = next(value for value in outcomes if value != "conflict")
    assert item.status == winner and item.revision == revision + 1
    assert item.approvals.count() == (1 if winner == "approved" else 0)
    assert CompanyBudgetReservation.objects.filter(
        item=item, status="reserved"
    ).count() == (1 if winner == "approved" else 0)
    assert not RentalInventoryDayLock.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_consent_withdrawal_and_reserve_serialize_without_unreviewed_hold(cycle):
    require_postgres()
    item = create(cycle)
    for role in ["owner", "signer", "payer", "employee", "colleague"]:
        assert respond(cycle, item, role).status_code == 200
    item.refresh_from_db()
    revision = item.revision
    reserve_body = command(expected_revision=revision)
    withdraw_body = command(
        expected_revision=revision,
        snapshot_digest=item.snapshot_digest,
        role="employee",
        decision="withdrawn",
        reason="My accommodation plan changed",
    )
    paths = ["reserve", "respond"]
    actors = [cycle["coordinator"], cycle["employee"]]
    bodies = [reserve_body, withdraw_body]
    responses = parallel_calls(
        lambda index: authenticated(actors[index]).post(
            API + f"company-contract-preparations/{item.id}/{paths[index]}/",
            bodies[index],
            format="json",
        )
    )
    assert sorted(r.status_code for r in responses) == [200, 409]
    item.refresh_from_db()
    item.booking.refresh_from_db()
    consent = item.consents.get(
        actor=cycle["employee"], role="employee", snapshot_digest=item.snapshot_digest
    )
    if responses[0].status_code == 200:
        assert consent.decision == "accepted"
        assert item.booking.status == "held"
        assert RentalInventoryDayLock.objects.exists()
    else:
        assert consent.decision == "withdrawn"
        assert item.state == "changes_requested"
        assert not item.booking.hold_id
        assert not RentalInventoryDayLock.objects.exists()
    assert item.revision == revision + 1
    assert not Lease.objects.exists() and not PaymentAttempt.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_parallel_original_reserve_retry_returns_one_hold_and_original_result(cycle):
    require_postgres()
    item = create(cycle)
    for role in ["owner", "signer", "payer", "employee", "colleague"]:
        assert respond(cycle, item, role).status_code == 200
    item.refresh_from_db()
    body = command(expected_revision=item.revision)
    path = API + f"company-contract-preparations/{item.id}/reserve/"
    responses = parallel_calls(
        lambda _: authenticated(cycle["coordinator"]).post(path, body, format="json")
    )
    assert [r.status_code for r in responses] == [200, 200]
    assert responses[0].data == responses[1].data
    item.refresh_from_db()
    item.booking.refresh_from_db()
    assert item.booking.hold_id
    assert item.booking.hold.day_locks.count() == RentalInventoryDayLock.objects.count()
    replay = authenticated(cycle["coordinator"]).post(path, body, format="json")
    assert replay.status_code == 200 and replay.data == responses[0].data
    assert not Lease.objects.exists() and not PaymentAttempt.objects.exists()
