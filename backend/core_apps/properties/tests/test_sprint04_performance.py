"""Availability projections load closure facts once, including Cairo DST boundaries."""

from datetime import date, time, timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from core_apps.properties.models import (
    AvailabilityClosure,
    PropertyVisit,
    OwnerAvailabilitySlot,
)
from core_apps.properties.services.availability_closures import (
    closure_intervals,
    slot_in_closure,
)
from core_apps.properties.services.viewing_times import availability, instant
from core_apps.properties.tests.test_views import _create_published_property
from core_apps.admin_api.tests.test_sprint04_performance import measured

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("size", [1, 56, 1000])
def test_closure_query_budget_and_half_open_boundaries(size, user):
    prop = _create_published_property(owner=user, price=1000)
    day = timezone.localdate() + timedelta(days=1)
    AvailabilityClosure.objects.create(
        property=prop, starts_at=instant(day, time(10)), ends_at=instant(day, time(12))
    )
    intervals = closure_intervals(prop)
    with CaptureQueriesContext(connection) as queries:
        for _ in range(size):
            assert not slot_in_closure(prop, day, time(9), intervals=intervals)
            assert slot_in_closure(prop, day, time(10), intervals=intervals)
            assert not slot_in_closure(prop, day, time(12), intervals=intervals)
    assert len(queries) == 0


@pytest.mark.parametrize("size", [1, 56, 1000])
def test_availability_window_and_constant_query_budget(size, user, another_user):
    prop = _create_published_property(owner=user, price=1000)
    visit = PropertyVisit.objects.create(
        property=prop, tenant=another_user, status="confirmed"
    )
    first_day = timezone.localdate() + timedelta(days=1)
    OwnerAvailabilitySlot.objects.bulk_create(
        [
            OwnerAvailabilitySlot(
                property=prop,
                owner=user,
                date=first_day + timedelta(days=i // 12),
                time=time(8 + i % 12),
            )
            for i in range(size)
        ]
    )
    data, report = measured(
        "appointment-availability", size, lambda: availability(visit)
    )
    assert len(data[0]) == size
    assert report["queries"] <= 4


def test_prepared_and_sql_closure_results_match_through_cairo_dst(user):
    prop = _create_published_property(owner=user, price=1000)
    intervals = closure_intervals(prop)
    for day, at in [
        (date(2026, 4, 24), time(0, 30)),
        (date(2026, 10, 29), time(23, 30)),
        (date(2026, 4, 24), time(1)),
        (date(2026, 10, 30), time(1)),
    ]:
        assert slot_in_closure(prop, day, at, intervals=intervals) == slot_in_closure(
            prop, day, at
        )
