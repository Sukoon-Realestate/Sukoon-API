"""Housing suggestions allow other locations but retain inventory authority."""

from copy import deepcopy
import uuid

import pytest

from core_apps.features.planning_models import HousingOffer
from core_apps.features.services.planning_parts.selection_payload import (
    selection_payload,
)
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from core_apps.properties.models import City, District, Property
from .test_funded_settlement import command
from .test_planning_cycles import API, configured_planning_offer, criteria_for, post
from .test_rental_phase2 import authenticated, rental_participants

pytestmark = pytest.mark.django_db


def another_property(prop, **changes):
    values = {
        "owner": prop.owner,
        "title": "Another home",
        "property_type": prop.property_type,
        "governorate": prop.governorate,
        "city": prop.city,
        "status": Property.Status.VERIFIED,
        "is_verified": True,
        "is_ownership_verified": True,
        "rental_inventory": deepcopy(prop.rental_inventory),
    }
    return Property.objects.create(**{**values, **changes})


def publish_and_body(tenant, prop, offer_id, **criteria_changes):
    request = post(
        tenant,
        "housing-requests/",
        command(
            action="publish",
            title="Looking for a home",
            criteria={**criteria_for(prop), **criteria_changes},
        ),
        201,
    ).data["resource"]
    _, snapshot = resolve_offer_snapshot(prop, offer_id, 2)
    return API + f"housing-requests/{request['id']}/offers/", command(
        request_id=request["id"],
        request_revision=request["revision"],
        selection=selection_payload(snapshot),
    )


@pytest.mark.parametrize("different_city", [False, True])
def test_city_and_district_preferences_do_not_block_an_offer(
    rental_participants, different_city
):
    owner, tenant, _, prop, offer_id = rental_participants
    city = (
        City.objects.create(name="Requested city", governorate=prop.governorate)
        if different_city
        else prop.city
    )
    district = District.objects.create(name="Requested district", city=city)
    endpoint, body = publish_and_body(
        tenant,
        prop,
        offer_id,
        city_id=str(city.id),
        district_ids=[str(district.id)],
    )
    response = authenticated(owner).post(endpoint, body, format="json")
    assert response.status_code == 201, response.data
    offer = HousingOffer.objects.get()
    assert offer.property_id == prop.pk
    assert offer.request.criteria["city_id"] == str(city.id)
    assert offer.request.criteria["district_ids"] == [str(district.id)]


def test_property_picker_filters_before_pagination_without_exposing_other_owners(
    rental_participants,
):
    owner, _, other, prop, _ = rental_participants
    another_property(prop, status=Property.Status.UNDER_REVIEW, is_verified=False)
    another_property(prop, is_ownership_verified=False)
    another_property(prop, is_verified=False)
    another_property(prop, owner=other)
    client = authenticated(owner)
    response = client.get(
        "/api/v1/properties/owned/",
        {"housing_offer_eligible": "true", "page_size": 1},
    )
    assert response.status_code == 200, response.data
    assert response.data["count"] == 1
    assert [row["id"] for row in response.data["results"]] == [str(prop.id)]
    assert client.get("/api/v1/properties/owned/").data["count"] == 4


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", Property.Status.UNDER_REVIEW),
        ("status", Property.Status.HIDDEN),
        ("is_verified", False),
        ("is_ownership_verified", False),
    ],
)
def test_changed_eligibility_returns_an_actionable_arabic_error(
    rental_participants, field, value
):
    owner, tenant, _, prop, offer_id = rental_participants
    another_property(prop)
    endpoint, body = publish_and_body(tenant, prop, offer_id)
    setattr(prop, field, value)
    prop.save(update_fields=[field])
    response = authenticated(owner).post(
        endpoint, body, format="json", HTTP_ACCEPT_LANGUAGE="ar"
    )
    assert response.status_code == 400, response.data
    assert "اعتماد نشر العقار وتوثيق ملكيته" in response.json()["message"]
    assert "No Property" not in response.json()["message"]
    assert not HousingOffer.objects.exists()


@pytest.mark.parametrize("missing", [False, True])
def test_foreign_or_removed_property_does_not_leak_a_model_lookup_error(
    rental_participants, missing
):
    owner, tenant, other, prop, offer_id = rental_participants
    endpoint, body = publish_and_body(tenant, prop, offer_id)
    body["selection"]["property_id"] = str(
        uuid.uuid4() if missing else another_property(prop, owner=other).id
    )
    response = authenticated(owner).post(
        endpoint, body, format="json", HTTP_ACCEPT_LANGUAGE="ar"
    )
    assert response.status_code == 404
    assert "العقار المختار لم يعد متاحًا" in response.json()["message"]
    assert not HousingOffer.objects.exists()


def test_different_accommodation_scope_still_has_a_localized_validation_error(
    rental_participants,
):
    owner, tenant, _, prop, offer_id = rental_participants
    endpoint, body = publish_and_body(tenant, prop, offer_id, rental_scope="bed")
    response = authenticated(owner).post(
        endpoint, body, format="json", HTTP_ACCEPT_LANGUAGE="ar"
    )
    assert response.status_code == 400
    assert "نوع السكن المختار" in response.json()["message"]
    assert "city" not in response.json()["message"]
    assert not HousingOffer.objects.exists()


@pytest.mark.parametrize(
    "language,expected",
    [
        ("ar", "العقار المختار لم يعد متاحًا"),
        ("en", "The selected property is unavailable."),
    ],
)
def test_removed_property_details_returns_useful_picker_error(
    rental_participants, language, expected
):
    owner = rental_participants[0]
    response = authenticated(owner).get(
        f"/api/v1/properties/{uuid.uuid4()}/",
        HTTP_ACCEPT_LANGUAGE=language,
    )
    assert response.status_code == 404
    assert expected in response.json()["message"]
