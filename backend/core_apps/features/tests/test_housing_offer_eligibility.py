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


def matching_room(prop, offer_id):
    room_id = str(uuid.uuid4())
    from core_apps.properties.models import PropertyType

    prop.property_type = PropertyType.objects.get(slug="apartment")
    prop.has_wifi = True
    prop.is_furnished = True
    prop.rental_inventory["mode"] = "rooms"
    prop.rental_inventory["rooms"] = [
        {"id": room_id, "name": "غرفة هادئة", "capacity": 1, "beds": []}
    ]
    offer = prop.rental_inventory["offers"][0]
    offer.update(
        rental_scope="room", room_ids=[room_id], capacity=1, name="الغرفة المطلوبة"
    )
    offer["terms"].update(price="5000", price_period="yearly", deposit="none")
    for field, value in [
        ("rental_scope", "entire_property"),
        ("capacity", 0),
        ("availability", "unavailable"),
    ]:
        alternative = deepcopy(offer)
        alternative.update(id=str(uuid.uuid4()), **{field: value})
        prop.rental_inventory["offers"].append(alternative)
    for field, value in [("price", "20000"), ("price_period", "monthly")]:
        alternative = deepcopy(offer)
        alternative["id"] = str(uuid.uuid4())
        alternative["terms"][field] = value
        prop.rental_inventory["offers"].append(alternative)
    prop.save()
    return {
        "rental_scope": "room",
        "people": 1,
        "price_period": "yearly",
        "budget_min": {"amount_minor": 90000, "currency": "EGP", "exponent": 2},
        "budget_max": {"amount_minor": 900000, "currency": "EGP", "exponent": 2},
        "amenities": ["wifi"],
        "furnished": True,
        "area_note": "بجوار الجامعة",
    }


def test_matching_room_cycle_preserves_all_requirements_and_exact_offer(
    rental_participants,
):
    owner, tenant, other, prop, offer_id = rental_participants
    requirements = matching_room(prop, offer_id)
    endpoint, body = publish_and_body(tenant, prop, offer_id, **requirements)
    request_id = body["request_id"]
    client = authenticated(owner)
    details = client.get(
        API + f"housing-requests/{request_id}/", HTTP_ACCEPT_LANGUAGE="ar"
    )
    criteria = details.data["criteria"]
    assert criteria["property_type_label"] == "شقة"
    assert criteria["amenity_labels"] == ["واي فاي"]
    assert criteria["people"] == 1
    assert criteria["area_note"] == "بجوار الجامعة"
    assert criteria["filters"]["rental_scope"] == "room"
    assert criteria["filters"]["is_furnished"] == "true"
    assert criteria["filters"]["price_period"] == "yearly"
    inventory_url = API + f"housing-requests/{request_id}/offer-inventory/{prop.id}/"
    inventory = client.get(inventory_url)
    assert inventory.status_code == 200, inventory.data
    assert [offer["id"] for offer in inventory.data["rental_inventory"]["offers"]] == [
        offer_id
    ]
    assert authenticated(tenant).get(inventory_url).status_code == 403
    assert authenticated(other).get(inventory_url).status_code in (403, 404)
    response = client.post(endpoint, body, format="json")
    assert response.status_code == 201, response.data
    offer = response.data["resource"]
    assert offer["selection"]["offer_id"] == offer_id
    shown = authenticated(tenant).get(endpoint)
    assert shown.status_code == 200
    assert shown.data["results"][0]["id"] == offer["id"]
    selected = post(
        tenant,
        f"housing-offers/{offer['id']}/select_to_proceed/",
        command(offer["revision"], decision="select_to_proceed"),
        409,
    )
    assert selected.data["message"].code == "action_retired"


def test_request_aware_property_picker_and_final_check_share_requirements(
    rental_participants,
):
    from core_apps.properties.models import PropertyType

    owner, tenant, _, prop, offer_id = rental_participants
    requirements = matching_room(prop, offer_id)
    endpoint, body = publish_and_body(tenant, prop, offer_id, **requirements)
    villa = PropertyType.objects.get(slug="villa")
    another_property(prop, property_type=villa, has_wifi=True, is_furnished=True)
    another_property(prop, has_wifi=False, is_furnished=True)
    another_property(prop, has_wifi=True, is_furnished=False)
    response = authenticated(owner).get(
        "/api/v1/properties/owned/",
        {"housing_request_id": body["request_id"], "page_size": 1},
    )
    assert response.status_code == 200, response.data
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(prop.id)
    # A valid choice becoming incompatible is still rejected on submission.
    prop.property_type = villa
    prop.save(update_fields=["property_type"])
    rejected = authenticated(owner).post(
        endpoint, body, format="json", HTTP_ACCEPT_LANGUAGE="ar"
    )
    assert rejected.status_code == 400
    assert "نوع العقار لا يطابق" in rejected.json()["message"]
    assert "does not match" not in rejected.json()["message"]
    assert not HousingOffer.objects.exists()
