import uuid
import pytest
from rest_framework.exceptions import ValidationError
from core_apps.properties.models import City, District
from core_apps.features.planning_models import HousingRequest
from core_apps.features.services.planning_parts.criteria import criteria
from core_apps.features.services.planning_parts.districts import district_matches
from core_apps.features.services.planning_parts.validate_payload_types import (
    criteria_payload,
)
from .test_rental_phase2 import authenticated, rental_participants
from .test_planning_cycles import criteria_for, configured_planning_offer, API
from .test_funded_settlement import command

pytestmark = pytest.mark.django_db


def test_matching_inventory_filter_uses_the_same_district_scope(rental_participants):
    from datetime import timedelta
    from django.utils import timezone

    owner, tenant, _, prop, _ = rental_participants
    first = District.objects.create(city=prop.city, name="First district")
    other = District.objects.create(city=prop.city, name="Other district")
    prop.district_catalog = first
    prop.save(update_fields=["district_catalog"])
    requests = []
    for selected in [[str(first.id)], [str(other.id)], []]:
        requests.append(
            HousingRequest.objects.create(
                user=tenant,
                title="Synthetic district demand",
                status="published",
                visibility="eligible_owners",
                criteria=criteria({**criteria_for(prop), "district_ids": selected}),
                expires_at=timezone.now() + timedelta(days=1),
            )
        )
    response = authenticated(owner).get(
        API + "housing-demand/", {"matching_inventory": "true"}
    )
    assert response.status_code == 200
    assert {row["id"] for row in response.data["results"]} == {
        str(requests[0].id),
        str(requests[2].id),
    }


def test_districts_publish_read_edit_and_unknown_receipt(rental_participants):
    owner, tenant, other, prop, _ = rental_participants
    rows = [District.objects.create(city=prop.city, name=name) for name in ["A", "B"]]
    raw = criteria_for(prop)
    raw["district_ids"] = [str(row.id) for row in rows]
    body = command(
        action="publish",
        title="District request",
        note="",
        visibility="eligible_owners",
        criteria=raw,
    )
    client = authenticated(tenant)
    response = client.post(API + "housing-requests/", body, format="json")
    assert response.status_code == 201, response.data
    resource = response.data["resource"]
    saved = HousingRequest.objects.get(id=resource["id"])
    assert saved.criteria["district_ids"] == raw["district_ids"]
    replay = client.post(API + "housing-requests/", body, format="json")
    assert (
        replay.status_code == 201
        and HousingRequest.objects.filter(user=tenant).count() == 1
    )
    detail = client.get(API + f"housing-requests/{saved.id}/").data
    assert detail["criteria"]["district_ids"] == raw["district_ids"]
    assert [row["name"] for row in detail["criteria"]["districts"]] == ["A", "B"]
    raw["district_ids"] = [str(rows[1].id)]
    edit = client.post(
        API + f"housing-requests/{saved.id}/edit/",
        command(saved.revision, action="edit", title="Changed", note="", criteria=raw),
        format="json",
    )
    assert edit.status_code == 200, edit.data
    assert edit.data["resource"]["criteria"]["district_ids"] == raw["district_ids"]


def test_reject_foreign_inactive_missing_and_malformed_districts(rental_participants):
    prop = rental_participants[3]
    city = City.objects.create(name="Other city", governorate=prop.governorate)
    foreign = District.objects.create(name="Foreign", city=city)
    inactive = District.objects.create(name="Inactive", city=prop.city, is_active=False)
    for values in [
        [str(foreign.id)],
        [str(inactive.id)],
        [str(uuid.uuid4())],
        "bad",
        [None],
        ["bad"],
    ]:
        with pytest.raises(ValidationError):
            criteria({**criteria_for(prop), "district_ids": values})


def test_legacy_reads_and_matching_do_not_guess_free_text(rental_participants):
    prop = rental_participants[3]
    district = District.objects.create(city=prop.city, name=prop.district)
    selected = criteria({**criteria_for(prop), "district_ids": [str(district.id)]})
    assert not district_matches(prop, selected)
    prop.district_catalog = district
    prop.save(update_fields=["district_catalog"])
    assert district_matches(prop, selected)
    district.is_active = False
    district.save(update_fields=["is_active"])
    projected = criteria_payload(selected)
    assert projected["districts"][0]["is_active"] is False
    assert projected["districts"][0]["name"] == district.name
    legacy = criteria_payload(
        {**selected, "district_ids": [], "area_note": "Unresolved old area"}
    )
    assert (
        legacy["district_scope"] == "all_city"
        and legacy["area_note"] == "Unresolved old area"
    )
    assert district_matches(prop, {})


def test_catalog_is_city_scoped_and_excludes_inactive(rental_participants):
    owner, tenant, other, prop, _ = rental_participants
    active = District.objects.create(city=prop.city, name="Current")
    District.objects.create(city=prop.city, name="Old", is_active=False)
    response = authenticated(tenant).get(
        f"/api/v1/properties/cities/{prop.city.id}/districts/"
    )
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [str(active.id)]


def test_owner_canonical_district_roundtrip_and_clear(rental_participants):
    from django.http import QueryDict
    from core_apps.properties.serializers.property_parts.property_serializer import (
        PropertySerializer,
    )
    from core_apps.properties.serializers.property_parts.property_detail_serializer import (
        PropertyDetailSerializer,
    )

    owner, tenant, other, prop, _ = rental_participants
    district = District.objects.create(city=prop.city, name="Synthetic district")
    serializer = PropertySerializer(
        prop, data={"district_catalog": str(district.id)}, partial=True
    )
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["district_catalog"] == district
    prop.district_catalog = district
    prop.district = district.name
    prop.save()
    assert str(PropertyDetailSerializer(prop).data["district_catalog"]) == str(
        district.id
    )
    payload = QueryDict("", mutable=True)
    payload["district_catalog"] = ""
    cleared = PropertySerializer(prop, data=payload, partial=True)
    assert cleared.is_valid(), cleared.errors
    assert cleared.validated_data["district_catalog"] is None
