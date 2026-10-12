"""Exercise the shared slot lock using independent PostgreSQL connections."""

from concurrent.futures import ThreadPoolExecutor
from datetime import time, timedelta
from threading import Barrier

import pytest
from django.db import connection, connections
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.properties.models import OwnerAvailabilitySlot, PropertyVisit
from .test_mobile_api_updates import create_property

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != "postgresql":
        pytest.skip("Visit booking races require PostgreSQL row locks")


@pytest.fixture
def booking_slot(another_user, apartment_type):
    property_obj = create_property(another_user, apartment_type)
    return OwnerAvailabilitySlot.objects.create(
        owner=another_user,
        property=property_obj,
        date=timezone.localdate() + timedelta(days=3),
        time=time(14),
    )


def parallel_requests(first, second):
    barrier = Barrier(2)

    def run(call):
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SET lock_timeout = '5s'")
            barrier.wait(timeout=10)
            return call()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, call) for call in (first, second)]
        return [future.result(timeout=20) for future in futures]


def book(user, slot):
    client = APIClient()
    client.force_authenticate(user=user)
    return client.post(
        reverse("property-visit-create", kwargs={"property_id": slot.property.id}),
        {"visit_date": slot.date.isoformat(), "visit_time": slot.time.isoformat()},
        format="json",
    )


def test_simultaneous_tenants_cannot_book_the_same_slot(user, superuser, booking_slot):
    responses = parallel_requests(
        lambda: book(user, booking_slot), lambda: book(superuser, booking_slot)
    )

    assert sorted(response.status_code for response in responses) == [201, 400]
    rejected = next(response for response in responses if response.status_code == 400)
    assert "already booked" in rejected.json()["message"]
    visit = PropertyVisit.objects.get()
    assert visit.tenant_id in {user.pk, superuser.pk}
    assert visit.property_id == booking_slot.property_id
    assert visit.status == PropertyVisit.Status.PENDING


@pytest.mark.parametrize("edit", ["disable", "remove"])
def test_schedule_edit_cannot_invalidate_concurrent_booking(
    user, another_user, booking_slot, edit
):
    def edit_schedule():
        owner_client = APIClient()
        owner_client.force_authenticate(user=another_user)
        return owner_client.put(
            reverse(
                "owner-availability-week",
                kwargs={"property_id": booking_slot.property.id},
            ),
            {
                "availability_date": booking_slot.date.isoformat(),
                "slots": (
                    [{"time": booking_slot.time.isoformat(), "is_enabled": False}]
                    if edit == "disable"
                    else []
                ),
            },
            format="json",
        )

    booking, edited = parallel_requests(lambda: book(user, booking_slot), edit_schedule)

    if booking.status_code == 201:
        visit = PropertyVisit.objects.get()
        assert visit.tenant_id == user.pk
        booking_slot.refresh_from_db()
        assert booking_slot.is_enabled is True
        assert edited.status_code == (400 if edit == "disable" else 200)
        if edit == "disable":
            assert "Booked visit slots cannot be disabled" in edited.json()["message"]
    else:
        assert booking.status_code == 400
        assert "not available" in booking.json()["message"]
        assert edited.status_code == 200
        assert not PropertyVisit.objects.exists()
        assert not OwnerAvailabilitySlot.objects.filter(
            pk=booking_slot.pk, is_enabled=True
        ).exists()
