import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import connection, connections

from core_apps.features.models import Lease, OwnerPayable, RentalInventoryDayLock
from core_apps.features.services.rental_phase2 import (
    RentalConflict,
    reserve_inventory_days,
)
from .test_current_cycle_contract import API, awaiting_signatures, create_checkout, sign
from .test_rental_phase2 import authenticated, rental_participants


def parallel_calls(call):
    barrier = Barrier(2)

    def run(index):
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SET lock_timeout = '5s'")
            barrier.wait(timeout=10)
            return call(index)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, index) for index in range(2)]
        return [future.result(timeout=20) for future in futures]


@pytest.mark.django_db(transaction=True)
def test_duplicate_mock_capture_posts_one_allocation_and_receipt(awaiting_signatures):
    if connection.vendor != "postgresql":
        pytest.skip("Row locking requires PostgreSQL")
    _, tenant, _, lease, sessions = awaiting_signatures
    for session in sessions:
        assert sign(session).status_code == 200
    attempt = create_checkout(tenant, lease.invoices.get())
    body = {
        "event": "captured",
        "expected_revision": attempt.revision,
        "request_key": str(uuid.uuid4()),
    }
    path = API + f"mock-provider/payment-attempts/{attempt.id}/events/"
    responses = parallel_calls(
        lambda _: authenticated(tenant).post(path, body, format="json")
    )
    assert [r.status_code for r in responses] == [200, 200]
    assert responses[0].data == responses[1].data
    attempt.refresh_from_db()
    assert attempt.invoice_allocation.amount_minor == 2_000_000
    assert attempt.receipt.payment_attempt_id == attempt.pk
    assert OwnerPayable.objects.filter(payment_attempt=attempt).count() == 1
    assert attempt.ledger_transactions.filter(kind="payment_captured").count() == 1


@pytest.mark.django_db(transaction=True)
def test_room_and_bed_overlapping_inventory_cannot_both_be_reserved(
    awaiting_signatures,
):
    if connection.vendor != "postgresql":
        pytest.skip("Row locking requires PostgreSQL")
    owner, tenant, _, initial, _ = awaiting_signatures
    initial.inventory_day_locks.all().delete()
    room_id, bed_id = str(uuid.uuid4()), str(uuid.uuid4())
    # Reservation now resolves canonical physical units, not arbitrary snapshot IDs.
    initial.property.rental_inventory = {
        "mode": "shared",
        "rooms": [{"id": room_id, "beds": [{"id": bed_id}]}],
    }
    initial.property.save(update_fields=["rental_inventory"])
    leases = [initial]
    initial.offer_id = str(uuid.uuid4())
    initial.offer_snapshot = {"rental_scope": "room", "room_ids": [room_id]}
    initial.save()
    leases.append(
        Lease.objects.create(
            property=initial.property,
            owner=owner,
            tenant=tenant,
            template_id=initial.template_id,
            template_version=initial.template_version,
            start_date=initial.start_date,
            end_date=initial.end_date,
            rent_amount_minor=initial.rent_amount_minor,
            legacy_read_only=False,
            offer_id=str(uuid.uuid4()),
            offer_snapshot={
                "rental_scope": "bed",
                "room_ids": [room_id],
                "bed_id": bed_id,
            },
        )
    )

    def reserve(index):
        try:
            reserve_inventory_days(
                leases[index],
                initial.start_date,
                initial.end_date,
                initial.hold_expires_at,
            )
            return "reserved"
        except RentalConflict:
            return "conflict"

    assert sorted(parallel_calls(reserve)) == ["conflict", "reserved"]
    assert (
        RentalInventoryDayLock.objects.filter(property=initial.property).count()
        == (initial.end_date - initial.start_date).days
    )
