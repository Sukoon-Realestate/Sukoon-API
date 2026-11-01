from datetime import time, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.common.contract_testing import api_json
from core_apps.properties.models import OwnerAvailabilitySlot, PropertyImage, PropertyVisit
from .test_mobile_api_updates import create_property

pytestmark = pytest.mark.django_db


@pytest.fixture
def availability(user, apartment_type):
    prop = create_property(user, apartment_type)
    client = APIClient()
    client.force_authenticate(user)
    today = timezone.localdate()
    week = today + timedelta(days=7 - today.weekday())
    data = {"week_start": week.isoformat(), "slots": [{"weekday": 1, "time": "12:00"}, {"weekday": 1, "time": "14:00"}]}
    return client, prop, week, data, f"/api/v1/properties/owner/properties/{prop.id}/availability/"


def test_preview_is_read_only_apply_is_additive_and_never_accepts_visits(availability, another_user):
    client, prop, week, data, path = availability
    visit = PropertyVisit.objects.create(property=prop, tenant=another_user, status="pending")
    response = client.post(path, data, format="json")
    assert response.status_code == 200
    assert not OwnerAvailabilitySlot.objects.exists()
    revision = response.json()["data"]["revision"]
    assert client.put(path, {**data, "revision": revision}, format="json").status_code == 200
    assert OwnerAvailabilitySlot.objects.count() == 2
    # Lost response: reading again shows the saved slots; resubmitting a stale
    # preview cannot duplicate or change them.
    assert client.put(path, {**data, "revision": revision}, format="json").status_code == 409
    fresh = client.post(path, data, format="json").json()["data"]
    assert {s["status"] for s in fresh["slots"]} == {"existing"}
    assert client.put(path, {**data, "revision": fresh["revision"]}, format="json").status_code == 200
    assert OwnerAvailabilitySlot.objects.count() == 2
    visit.refresh_from_db()
    assert visit.status == "pending" and visit.visit_date is None


def test_preview_rechecks_confirmed_conflicts_and_disabled_slots(availability, another_user):
    client, prop, week, data, path = availability
    revision = client.post(path, data, format="json").json()["data"]["revision"]
    PropertyVisit.objects.create(property=prop, tenant=another_user, status="confirmed", visit_date=week, visit_time=time(12))
    assert client.put(path, {**data, "revision": revision}, format="json").status_code == 409
    OwnerAvailabilitySlot.objects.create(property=prop, owner=prop.owner, date=week, time=time(14), is_enabled=False)
    preview = client.post(path, data, format="json").json()["data"]
    assert [s["status"] for s in preview["slots"]] == ["busy", "disabled"]
    assert client.put(path, {**data, "revision": preview["revision"]}, format="json").status_code == 200
    assert not OwnerAvailabilitySlot.objects.get().is_enabled


def test_availability_is_owner_only(availability, another_user):
    client, prop, week, data, path = availability
    client.force_authenticate(another_user)
    assert client.post(path, data, format="json").status_code == 403
    assert client.put(path, data, format="json").status_code == 403


@pytest.mark.parametrize("slot", [{"weekday": True, "time": "12:00"}, {"weekday": 8, "time": "12:00"}, {"weekday": 1, "time": "24:00"}, {"weekday": 1, "time": [12]}])
def test_availability_rejects_invalid_patterns(availability, slot):
    client, _, _, data, path = availability
    assert client.post(path, {**data, "slots": [slot]}, format="json").status_code == 400


def test_categories_preserve_cover_order_and_require_current_revision(user, another_user, apartment_type):
    prop = create_property(user, apartment_type)
    first = PropertyImage.objects.create(property=prop, image="room-one", position=0)
    second = PropertyImage.objects.create(property=prop, image="room-two", position=1)
    prop.main_image = first.image
    prop.save(update_fields=["main_image"])
    prop.refresh_from_db()
    data = {"image_ids": [str(first.id), str(second.id)], "main_image_id": str(first.id),
        "expected_revision": prop.media_revision, "categories": {str(second.id): "kitchen"}}
    client = APIClient()
    client.force_authenticate(user)
    path = f"/api/v1/properties/{prop.id}/images/order/"
    assert client.patch(path, data, format="json").status_code == 200
    second.refresh_from_db(); prop.refresh_from_db()
    assert second.room_category == "kitchen" and second.position == 1
    assert str(prop.main_image) == str(first.image)
    # Identical lost-response replay is harmless; changed stale content is not.
    assert client.patch(path, data, format="json").status_code == 200
    assert client.patch(path, {**data, "categories": {str(second.id): "bedroom"}}, format="json").status_code == 409
    assert client.patch(path, {**data, "categories": {str(second.id): []}}, format="json").status_code == 400
    client.force_authenticate(another_user)
    assert client.patch(path, data, format="json").status_code == 403


@pytest.mark.parametrize("owner", [True, False])
def test_agenda_day_filter_precedes_pagination_and_sorts_times(user, another_user, apartment_type, owner):
    prop = create_property(user, apartment_type)
    day = timezone.localdate() + timedelta(days=1)
    expected = None
    for hour in (17, 9, 13):
        visit = PropertyVisit.objects.create(property=prop, tenant=another_user, status="confirmed", visit_date=day, visit_time=time(hour))
        if hour == 9:
            expected = str(visit.id)
    PropertyVisit.objects.create(property=prop, tenant=another_user, status="confirmed", visit_date=day + timedelta(days=1), visit_time=time(8))
    client = APIClient(); client.force_authenticate(user if owner else another_user)
    response = client.get("/api/v1/properties/" + ("owner/" if owner else "") + "visits/requests/", {"visit_date": day.isoformat(), "status": "confirmed", "page_size": 1})
    assert response.status_code == 200
    data = api_json(response)["data"]
    assert data["count"] == 3
    assert data["results"][0]["id"] == expected
