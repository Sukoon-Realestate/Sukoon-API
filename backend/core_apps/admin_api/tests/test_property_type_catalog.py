from datetime import timedelta
from uuid import uuid4
import pytest
from django.db.models.deletion import ProtectedError
from django.utils import timezone, translation
from rest_framework.exceptions import ValidationError

from core_apps.admin_api.tests.test_content_editor import client, operator, save, ROOT
from core_apps.admin_api.tests.test_analytics_periods import home  # noqa: F401
from core_apps.features.services.planning_parts.criteria import criteria
from core_apps.features.services.planning_parts.validate_payload_types import (
    criteria_payload,
)
from core_apps.properties.models import PropertyType
from core_apps.admin_api.models import StaffProfile
from core_apps.properties.services import PropertyService
from core_apps.properties.catalog_labels import property_type_label
from core_apps.properties.serializers import (
    PropertySerializer,
    PropertyDetailSerializer,
)

pytestmark = pytest.mark.django_db


def test_versioned_type_editor_keeps_code_and_localizes_public_lists(api_client):
    api = client(operator())
    values = {
        "name": "Catalog garden home",
        "slug": "catalog-garden",
        "name_ar": "سكن بحديقة",
        "name_en": "Garden home",
        "description": "A descriptive type",
        "is_active": True,
        "sort_order": 1,
    }
    response, key = save(api, "property_types", values)
    assert response.status_code == 201, response.data
    identity = response.data["id"]
    replay, _ = save(api, "property_types", values, key=key)
    assert replay.data == response.data
    row = PropertyType.objects.get(id=identity)
    assert property_type_label(row, "ar") == "سكن بحديقة"
    assert property_type_label(row, "en") == "Garden home"
    for language, label in [("ar", "سكن بحديقة"), ("en", "Garden home")]:
        with translation.override(language):
            data = api_client.get(
                "/api/v1/properties/types/", HTTP_ACCEPT_LANGUAGE=language
            ).data
            listed = next(item for item in data["results"] if item["slug"] == row.slug)
            assert listed["name"] == label and listed["revision"] == 1
            option = next(
                item
                for item in PropertyService.get_filter_options(language)[
                    "property_types"
                ]
                if item["value"] == row.slug
            )
            assert option["label"] == label and option["id"] == identity
    changed, _ = save(
        api,
        "property_types",
        {"name_ar": "تسمية محدثة", "is_active": False},
        1,
        identity,
    )
    assert changed.status_code == 200 and changed.data["revision"] == 2
    assert not any(
        item["value"] == row.slug
        for item in PropertyService.get_filter_options("ar")["property_types"]
    )
    row.refresh_from_db()
    assert property_type_label(row, "ar") == "تسمية محدثة"
    stale, _ = save(api, "property_types", {"name_ar": "قديم"}, 1, identity)
    assert stale.status_code == 409
    changed_code, _ = save(
        api, "property_types", {"slug": "different-code"}, 2, identity
    )
    assert changed_code.status_code == 400
    assert api.get(ROOT + f"property_types/{identity}/").data["history"]


def test_inactive_type_blocks_new_selection_but_preserves_existing_listing(
    home, another_user  # noqa: F811
):
    kind = home.property_type
    PropertyType.objects.filter(pk=kind.pk).update(is_active=False, name_ar="نوع محفوظ")
    kind.refresh_from_db()
    with translation.override("ar"):
        detail = PropertyDetailSerializer(home).data
    assert detail["property_type"] == kind.slug
    assert detail["property_type_catalog"]["name"] == "نوع محفوظ"
    assert detail["property_type_catalog"]["is_active"] is False
    update = PropertySerializer(
        home, data={"title": "Updated title", "property_type": kind.slug}, partial=True
    )
    assert update.is_valid(), update.errors
    PropertyService.update_property(home, update.validated_data)
    home.refresh_from_db()
    assert home.property_type_id == kind.pk
    with pytest.raises(ValidationError, match="catalog choice"):
        PropertyService.create_property(
            another_user,
            {
                "title": "New listing",
                "property_type": kind,
                "city": home.city,
                "governorate": home.governorate,
            },
        )
    with pytest.raises(ProtectedError):
        kind.delete()


def test_housing_request_type_is_current_on_new_selection_and_historical_on_read(
    home,  # noqa: F811
):
    kind = home.property_type
    raw = {
        "city_id": str(home.city.id),
        "start_on": str(timezone.localdate() + timedelta(days=2)),
        "property_type": kind.slug,
    }
    stored = criteria(raw)
    PropertyType.objects.filter(pk=kind.pk).update(
        is_active=False, name_en="Historical type"
    )
    with pytest.raises(ValidationError, match="catalog choice"):
        criteria(raw)
    retained = criteria(raw, previous=stored)
    assert retained["property_type"] == kind.slug
    with translation.override("en"):
        projection = criteria_payload(
            stored, catalog=PropertyService.get_filter_options("en")
        )
    assert projection["property_type_label"] == "Historical type"
    with pytest.raises(ValidationError):
        criteria({**raw, "property_type": "not-an-existing-type"})


def test_stale_validated_type_is_rechecked_when_listing_is_saved(
    home, another_user  # noqa: F811
):
    kind = PropertyType.objects.create(name="New selectable", slug="new-selectable")
    serializer = PropertySerializer(
        home, data={"property_type": kind.slug}, partial=True
    )
    assert serializer.is_valid(), serializer.errors
    PropertyType.objects.filter(pk=kind.pk).update(is_active=False)
    with pytest.raises(ValidationError):
        PropertyService.update_property(home, serializer.validated_data)
    home.refresh_from_db()
    assert home.property_type_id != kind.pk


def test_selector_catalog_does_not_drop_choices_after_first_page(api_client):
    existing = set(
        PropertyType.objects.filter(is_active=True).values_list("slug", flat=True)
    )
    PropertyType.objects.bulk_create(
        [
            PropertyType(name=f"Type {i}", slug=f"type-{i}", sort_order=i)
            for i in range(35)
        ]
    )
    PropertyType.objects.create(name="Unavailable", slug="unavailable", is_active=False)
    data = api_client.get("/api/v1/properties/types/").data
    assert data["count"] == len(existing) + 35 and data["next"] is None
    assert {item["slug"] for item in data["results"]} == existing | {
        f"type-{i}" for i in range(35)
    }
    assert [
        item["slug"] for item in data["results"] if item["slug"].startswith("type-")
    ] == [f"type-{i}" for i in range(35)]


def test_admin_filters_use_catalog_identity_and_include_retired_history(
    home, api_client, user  # noqa: F811
):
    StaffProfile.objects.create(user=user, role_name="property_reviewer")
    api_client.force_authenticate(user)
    kind = home.property_type
    PropertyType.objects.filter(pk=kind.pk).update(
        name_ar="اسم إداري محدث", is_active=False
    )
    same_label = PropertyType.objects.create(
        name="Different catalog identity",
        slug="other-identity",
        name_ar="اسم إداري محدث",
    )
    metrics = api_client.get(
        "/api/v1/admin/properties/metrics/", HTTP_ACCEPT_LANGUAGE="ar"
    )
    assert metrics.status_code == 200
    option = next(
        row for row in metrics.data["propertyTypes"] if row["id"] == str(kind.id)
    )
    assert option["name"] == "اسم إداري محدث" and option["is_active"] is False
    target = "/api/v1/admin/properties/"
    found = api_client.get(
        target, {"property_type_id": str(kind.id)}, HTTP_ACCEPT_LANGUAGE="ar"
    )
    assert found.status_code == 200 and found.data["count"] == 1
    assert found.data["results"][0]["id"] == str(home.id)
    assert found.data["results"][0]["type"] == "اسم إداري محدث"
    for identity in [same_label.id, uuid4()]:
        result = api_client.get(target, {"property_type_id": str(identity)})
        assert result.status_code == 200 and result.data["count"] == 0
    for identity in ["not-a-uuid", "", str(kind.pk)]:
        assert api_client.get(target, {"property_type_id": identity}).status_code == 400
    StaffProfile.objects.filter(user=user).update(role_name="support")
    assert api_client.get(target, {"property_type_id": str(kind.id)}).status_code == 403
    assert api_client.get("/api/v1/admin/properties/metrics/").status_code == 403
