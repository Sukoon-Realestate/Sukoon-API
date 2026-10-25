"""Concurrent requests stay distinct by tenant without scheduling slots."""

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
def booking_property(another_user, apartment_type):
    return create_property(another_user, apartment_type)


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


def book(user, prop):
    client = APIClient()
    client.force_authenticate(user=user)
    return client.post(reverse("property-visit-create", kwargs={"property_id": prop.id}), {"note": "Arrange in chat"}, format="json")


def test_different_tenants_can_request_the_same_property(user, superuser, booking_property):
    responses = parallel_requests(lambda: book(user, booking_property), lambda: book(superuser, booking_property))
    assert sorted(r.status_code for r in responses) == [201, 201]
    assert PropertyVisit.objects.count() == 2
    assert not PropertyVisit.objects.exclude(visit_date=None, visit_time=None).exists()


def test_same_tenant_concurrent_duplicate_creates_one_request(user, booking_property):
    responses = parallel_requests(lambda: book(user, booking_property), lambda: book(user, booking_property))
    assert sorted(r.status_code for r in responses) == [201, 400]
    assert PropertyVisit.objects.count() == 1
