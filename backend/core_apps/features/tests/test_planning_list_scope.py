"""Planning collections select their parent and kind before pagination."""
import copy
import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.features.planning_models import (
    ConditionReport, HousingOffer, HousingRequest, TenancyTransition,
)
from core_apps.users.models import User
from .test_rental_phase3 import phase3_lease  # noqa: F401

API = "/api/v1/features/v1/"


@pytest.mark.django_db
@pytest.mark.parametrize("collection,kind", [
    ("condition-reports", "move_in"),
    ("move-out-notices", "moveOutNotice"),
    ("replacement-requests", "replacement"),
])
def test_lease_collections_filter_parent_kind_and_account(phase3_lease, collection, kind):
    owner, tenant, first = phase3_lease
    second = copy.copy(first)
    second.pk = None
    second.id = uuid.uuid4()
    second.offer_id = str(uuid.uuid4())
    second.save(force_insert=True)
    expected = None
    for lease in (first, second):
        if collection == "condition-reports":
            item = ConditionReport.objects.create(
                lease=lease, author=tenant, kind=kind,
                inspected_on=timezone.localdate(),
            )
        else:
            item = TenancyTransition.objects.create(
                lease=lease, author=tenant, kind=kind,
                requested_on=timezone.localdate(), reason="Scope fixture",
            )
            TenancyTransition.objects.create(
                lease=lease, author=tenant,
                kind="replacement" if kind == "moveOutNotice" else "moveOutNotice",
                requested_on=timezone.localdate(), reason="Other kind",
            )
        if lease == first:
            expected = str(item.id)
    path = API + f"leases/{first.id}/{collection}/"
    client = APIClient()
    for actor in (owner, tenant):
        client.force_authenticate(actor)
        response = client.get(path, {"page_size": 1})
        assert response.status_code == 200, response.data
        payload = response.json()["data"]
        assert int(response["X-Total-Count"]) == 1
        assert [item["id"] for item in payload] == [expected]
        assert payload[0]["lease_id"] == str(first.id)
        assert payload[0]["kind"] == kind
    outsider = User.objects.create_user(email="planning-outsider@example.test", is_verified=True)
    client.force_authenticate(outsider)
    assert client.get(path).status_code == 404


@pytest.mark.django_db
def test_housing_offers_filter_request_before_pagination(phase3_lease):
    owner, tenant, lease = phase3_lease
    requests = [HousingRequest.objects.create(
        user=tenant, title=f"Request {number}",
        expires_at=timezone.now() + timedelta(days=7),
    ) for number in range(2)]
    offers = [HousingOffer.objects.create(
        request=parent, owner=owner, property=lease.property,
        request_revision=1, rent_minor=10000, price_period="monthly",
    ) for parent in requests]
    client = APIClient()
    client.force_authenticate(tenant)
    response = client.get(API + f"housing-requests/{requests[0].id}/offers/", {"page_size": 1})
    assert response.status_code == 200, response.data
    payload = response.json()["data"]
    assert int(response["X-Total-Count"]) == 1
    assert [item["id"] for item in payload] == [str(offers[0].id)]
    assert payload[0]["request_id"] == str(requests[0].id)
    requests[0].visibility = "private"
    requests[0].save(update_fields=["visibility"])
    outsider = User.objects.create_user(email="offer-outsider@example.test", is_verified=True)
    client.force_authenticate(outsider)
    assert client.get(API + f"housing-requests/{requests[0].id}/offers/").status_code == 404
