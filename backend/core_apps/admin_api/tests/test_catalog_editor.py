"""Catalog edits are versioned, public-ID based and safe for existing contracts."""

from datetime import date, timedelta
from uuid import uuid4
import pytest
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from core_apps.admin_api.tests.test_content_editor import client, operator, save, ROOT
from core_apps.common.content_models import ContentEditAudit
from core_apps.properties.models import Governorate, City, District
from core_apps.properties.catalog_access import require_current_selection
from core_apps.properties.catalog_labels import location_label
from core_apps.properties.services.moderation import version
from core_apps.profiles.serializers_parts.profile_edit_serializer import (
    ProfileEditSerializer,
)
from core_apps.profiles.models import Profile
from core_apps.features.student_models import University, Campus
from core_apps.features.services.student_housing.plans import validate_destinations
from core_apps.features.services.student_housing.profiles import campus_payload
from core_apps.features.services.planning_parts.criteria import criteria
from core_apps.features.tests.test_rental_phase2 import rental_participants  # noqa: F401
from core_apps.features.tests.test_planning_cycles import criteria_for

pytestmark = pytest.mark.django_db


def test_catalog_pagination_preserves_http_headers_for_both_dashboards():
    api = client(operator())
    Governorate.objects.bulk_create([Governorate(name=f"Pagination {n}", slug=f"pagination-{n}") for n in range(29)])
    response = api.get(ROOT + "governorates/?page=1")
    assert response.status_code == 200
    assert len(response.data["results"]) == 25
    assert response.headers["X-Per-Page"] == "25"
    assert response.headers["X-Total-Pages"] == "2"
    second = api.get(ROOT + "governorates/?page=2")
    assert len(second.data["results"]) == 4


def location(name, **extra):
    return {
        "name": name,
        "name_ar": "اسم اختبار",
        "name_en": name,
        "is_active": True,
        "sort_order": 0,
        **extra,
    }


def academic(**extra):
    return {
        "name_ar": "جامعة اختبار",
        "name_en": "Test university",
        "active": True,
        "sort_order": 1,
        "source_url": "https://example.test/reviewed",
        "checked_on": date.today().isoformat(),
        **extra,
    }


def created(api, kind, values):
    result, _ = save(api, kind, values)
    assert result.status_code == 201, result.data
    return result.data


def test_shared_catalogs_use_public_ids_translations_versions_and_recovery(api_client):
    api = client(operator())
    schemas = {row["kind"]: row for row in api.get(ROOT).data["catalogs"]}
    assert {
        "governorates",
        "cities",
        "districts",
        "universities",
        "campuses",
    } <= schemas.keys()
    assert (
        next(f for f in schemas["cities"]["fields"] if f["name"] == "governorate")[
            "relation"
        ]
        == "governorates"
    )
    governorate = created(api, "governorates", location("Catalog region"))
    city = created(
        api, "cities", location("Catalog city", governorate=governorate["id"])
    )
    district = created(api, "districts", location("Catalog district", city=city["id"]))
    row = City.objects.get(id=city["id"])
    assert city["values"]["governorate"] == governorate["id"]
    assert city["relation_labels"]["governorate"] == governorate["values"]["name_ar"]
    assert api.get(ROOT + f"cities/{row.pk}/").status_code == 404
    result, key = save(
        api,
        "cities",
        {"name_ar": "اسم جديد", "name_en": "New city name"},
        1,
        city["id"],
    )
    assert result.status_code == 200, result.data
    row.refresh_from_db()
    assert row.revision == 2 and row.slug == "catalog-city"
    assert (
        location_label(row, "ar") == "اسم جديد"
        and location_label(row, "en") == "New city name"
    )
    for language, name in [("ar", "اسم جديد"), ("en", "New city name")]:
        response = api_client.get(
            reverse("city-list"),
            {"governorate": governorate["id"], "lang": language},
            HTTP_X_APP_TYPE="mobile",
        )
        assert response.status_code == 200
        assert response.data["results"][0]["name"] == name
    receipt = api.post(
        ROOT + f"cities/receipts/{key}/", {"identity": city["id"]}, format="json"
    )
    assert receipt.data["receipt"] == result.data
    assert len(api.get(ROOT + f"cities/{city['id']}/").data["history"]) == 2
    assert save(api, "cities", {"name_ar": "قديم"}, 1, city["id"])[0].status_code == 409
    assert (
        save(api, "cities", {"is_active": False}, 2, city["id"])[0].status_code == 200
    )
    assert (
        api_client.get(reverse("city-list"), {"governorate": governorate["id"]}).data[
            "count"
        ]
        == 0
    )
    with pytest.raises(ValidationError):
        require_current_selection(District.objects.get(id=district["id"]))
    assert save(api, "cities", {"is_active": True}, 3, city["id"])[0].status_code == 200
    assert (
        api_client.get(reverse("city-list"), {"governorate": governorate["id"]}).data[
            "count"
        ]
        == 1
    )


def test_catalog_deactivation_keeps_property_profile_and_request_history(
    rental_participants,
):
    owner, tenant, _, prop, _ = rental_participants
    district = District.objects.create(city=prop.city, name="Historical district")
    prop.district_catalog = district
    prop.save(update_fields=["district_catalog"])
    prop.refresh_from_db()
    before = version(prop)
    raw = {**criteria_for(prop), "district_ids": [str(district.id)]}
    old = criteria(raw)
    profile = Profile.objects.get(user=tenant)
    profile.city = prop.city
    profile.save(update_fields=["city"])
    api = client(operator())
    assert (
        save(
            api,
            "cities",
            {"name_ar": "مدينة محدثة", "is_active": False},
            1,
            str(prop.city.id),
        )[0].status_code
        == 200
    )
    assert (
        save(
            api,
            "districts",
            {"name_en": "Renamed district", "is_active": False},
            1,
            str(district.id),
        )[0].status_code
        == 200
    )
    prop.refresh_from_db()
    assert version(prop) == before
    assert prop.city_id == profile.city_id and prop.district_catalog_id == district.pk
    # Retaining an old location does not make a price/budget/profile edit impossible.
    serializer = ProfileEditSerializer(
        profile, data={"city_id": str(prop.city.id)}, partial=True
    )
    assert serializer.is_valid(), serializer.errors
    assert criteria(raw, previous=old)["city_id"] == str(prop.city.id)
    with pytest.raises(ValidationError):
        criteria(raw)
    profile.city = None
    profile.save(update_fields=["city"])
    serializer = ProfileEditSerializer(
        profile, data={"city_id": str(prop.city.id)}, partial=True
    )
    assert not serializer.is_valid()
    # No hard deletion route can remove catalog history or related inventory.
    assert api.delete(ROOT + f"cities/{prop.city.id}/").status_code == 405
    assert City.objects.filter(pk=prop.city_id).exists()


def test_academic_catalog_validates_sources_coordinates_hierarchy_and_retained_choices(
    api_client,
):
    api = client(operator())
    gov = Governorate.objects.create(name="Campus region")
    city = City.objects.create(name="Campus city", governorate=gov)
    university = created(api, "universities", academic())
    campus = created(
        api,
        "campuses",
        academic(
            university=university["id"],
            city=str(city.id),
            latitude="30.1234567",
            longitude="31.1234567",
        ),
    )
    row = Campus.objects.get(id=campus["id"])
    assert row.university_id == University.objects.get(id=university["id"]).pk
    assert (
        save(api, "campuses", {"latitude": "91"}, 1, campus["id"])[0].status_code == 400
    )
    assert (
        save(api, "campuses", {"longitude": None}, 1, campus["id"])[0].status_code
        == 400
    )
    other = City.objects.create(name="Other campus city", governorate=gov)
    assert (
        save(api, "campuses", {"city": str(other.id)}, 1, campus["id"])[0].status_code
        == 400
    )
    invalid = academic(checked_on=(date.today() + timedelta(days=1)).isoformat())
    assert save(api, "universities", invalid)[0].status_code == 400
    assert (
        save(api, "universities", academic(source_url="http://example.test"))[
            0
        ].status_code
        == 400
    )
    assert (
        save(api, "universities", {"active": False}, 1, university["id"])[0].status_code
        == 200
    )
    retained = {"campus_ids": [str(row.id)]}
    with pytest.raises(ValidationError):
        validate_destinations(retained)
    assert validate_destinations(retained, retained) == retained
    row.refresh_from_db()
    assert campus_payload(row)["active"] is False
    assert campus_payload(row)["name"] == "Test university"
    assert (
        ContentEditAudit.objects.filter(kind="campuses", object_id=str(row.id)).count()
        == 1
    )


def test_catalog_rejects_new_children_under_stopped_parent_and_unknown_fields():
    api = client(operator())
    gov = Governorate.objects.create(name="Stopped", is_active=False)
    response, _ = save(api, "cities", location("Unavailable", governorate=str(gov.id)))
    assert (
        response.status_code == 400
        and not City.objects.filter(name="Unavailable").exists()
    )
    assert (
        save(api, "governorates", location("Unknown", financial_approver=True))[
            0
        ].status_code
        == 400
    )
    assert api.get(ROOT + f"campuses/{uuid4()}/").status_code == 404
    assert api.get(ROOT + "cities/not-an-id/").status_code == 404


def test_stale_profile_form_rechecks_catalog_inside_write_transaction(
    rental_participants,
):
    from core_apps.profiles.services import ProfileService

    tenant = rental_participants[1]
    prop = rental_participants[3]
    profile = Profile.objects.get(user=tenant)
    profile.city = None
    profile.save(update_fields=["city"])
    serializer = ProfileEditSerializer(
        profile, data={"city_id": str(prop.city.id)}, partial=True
    )
    assert serializer.is_valid(), serializer.errors
    api = client(operator())
    result, _ = save(api, "cities", {"is_active": False}, 1, str(prop.city.id))
    assert result.status_code == 200
    with pytest.raises(ValidationError):
        ProfileService.update_user_profile(tenant, serializer.validated_data)
    profile.refresh_from_db()
    assert profile.city is None
