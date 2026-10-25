"""Housing demand discovery is independent of offer inventory matching."""

import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from core_apps.features.planning_models import HousingOffer, HousingRequest
from core_apps.features.services.planning_parts.selection_payload import (
    selection_payload,
)
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from core_apps.properties.models import City
from .test_funded_settlement import command
from .test_planning_cycles import (
    API,
    configured_planning_offer,
    criteria_for,
    post,
)
from .test_rental_phase2 import authenticated, rental_participants


def publish(user, prop, *, city=None, title="Published housing request"):
    criteria = criteria_for(prop)
    if city is not None:
        criteria["city_id"] = str(city.id)
    return post(
        user,
        "housing-requests/",
        command(action="publish", title=title, criteria=criteria),
        201,
    ).data["resource"]


@pytest.mark.django_db
def test_owner_can_offer_verified_accommodation_across_cities(
    rental_participants,
):
    owner, tenant, stranger, prop, offer_id = rental_participants
    other_city = City.objects.create(
        name="Another demand city", governorate=prop.governorate
    )
    item = publish(tenant, prop, city=other_city)
    client = authenticated(owner)

    demand = client.get(API + "housing-demand/")
    assert demand.status_code == 200
    assert [row["id"] for row in demand.data["results"]] == [item["id"]]
    assert demand.data["results"][0]["criteria"]["city"]["id"] == str(other_city.id)
    assert demand.data["results"][0]["allowed_actions"] == ["offer"]
    detail = client.get(API + f"housing-requests/{item['id']}/")
    assert detail.status_code == 200
    assert detail.data["id"] == item["id"]
    grant = client.get(
        API + "planning-capabilities/",
        {"capability": "housing_requests", "subject_id": item["id"]},
    )
    assert set(grant.data["allowed_actions"]) == {"read", "offer"}

    _, snapshot = resolve_offer_snapshot(prop, offer_id, 2)
    body = command(
        request_id=item["id"],
        request_revision=item["revision"],
        selection=selection_payload(snapshot),
    )
    offered = post(owner, f"housing-requests/{item['id']}/offers/", body, 201)
    replay = post(owner, f"housing-requests/{item['id']}/offers/", body, 201)
    assert replay.data == offered.data
    assert HousingOffer.objects.count() == 1
    assert offered.data["resource"]["selection"]["property_id"] == str(prop.id)
    assert authenticated(stranger).get(API + "housing-demand/").status_code == 403
    assert (
        authenticated(stranger).get(API + f"housing-requests/{item['id']}/").status_code
        == 404
    )


@pytest.mark.django_db
def test_demand_city_filter_is_explicit_and_pagination_keeps_all_cities(
    rental_participants,
):
    owner, tenant, stranger, prop, _ = rental_participants
    other_city = City.objects.create(
        name="Second demand city", governorate=prop.governorate
    )
    matching = publish(tenant, prop)
    elsewhere = publish(stranger, prop, city=other_city)
    client = authenticated(owner)
    first = client.get(API + "housing-demand/", {"page_size": 1})
    second = client.get(API + "housing-demand/", {"page_size": 1, "page": 2})
    assert first.status_code == second.status_code == 200
    assert first.data["count"] == second.data["count"] == 2
    assert [row["id"] for row in first.data["results"]] == [elsewhere["id"]]
    assert [row["id"] for row in second.data["results"]] == [matching["id"]]

    selected = client.get(API + "housing-demand/", {"city": str(prop.city.id)})
    assert selected.status_code == 200
    assert [row["id"] for row in selected.data["results"]] == [matching["id"]]
    assert selected.data["results"][0]["allowed_actions"] == ["offer"]
    selected = client.get(API + "housing-demand/", {"city": str(other_city.id).upper()})
    assert [row["id"] for row in selected.data["results"]] == [elsewhere["id"]]
    assert client.get(API + "housing-demand/", {"city": "Cairo"}).status_code == 400
    assert (
        client.get(API + "housing-demand/", {"city": str(uuid.uuid4())}).data["results"]
        == []
    )


@pytest.mark.django_db
def test_demand_excludes_own_unpublished_expired_and_nonpublic_requests(
    rental_participants,
):
    owner, tenant, _, prop, _ = rental_participants
    visible = publish(tenant, prop)
    publish(owner, prop)
    reference = HousingRequest.objects.get(id=visible["id"])
    hidden = []
    for status in ["draft", "paused", "closed", "fulfilled", "expired"]:
        hidden.append(
            HousingRequest.objects.create(
                user=tenant,
                title=status,
                status=status,
                criteria=reference.criteria,
                expires_at=reference.expires_at,
            )
        )
    hidden.append(
        HousingRequest.objects.create(
            user=tenant,
            title="Past expiry",
            criteria=reference.criteria,
            expires_at=timezone.now() - timedelta(seconds=1),
        )
    )
    hidden.append(
        HousingRequest.objects.create(
            user=tenant,
            title="Not disclosed to owners",
            visibility="private",
            criteria=reference.criteria,
            expires_at=reference.expires_at,
        )
    )
    client = authenticated(owner)
    response = client.get(API + "housing-demand/")
    assert [row["id"] for row in response.data["results"]] == [visible["id"]]
    for item in hidden:
        assert client.get(API + f"housing-requests/{item.id}/").status_code == 404
        assert (
            authenticated(tenant).get(API + f"housing-requests/{item.id}/").status_code
            == 200
        )


@pytest.mark.django_db
def test_ineligible_owner_cannot_read_demand_after_listing_verification_is_removed(
    rental_participants,
):
    owner, tenant, _, prop, _ = rental_participants
    item = publish(tenant, prop)
    prop.is_ownership_verified = False
    prop.save(update_fields=["is_ownership_verified"])
    client = authenticated(owner)
    assert client.get(API + "housing-demand/").status_code == 403
    assert client.get(API + f"housing-requests/{item['id']}/").status_code == 404
