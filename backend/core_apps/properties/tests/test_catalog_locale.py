import pytest
from rest_framework.test import APIClient, APIRequestFactory
from core_apps.properties.models import PropertyType, Governorate, City
from core_apps.properties.serializers import PropertyTypeSerializer
from core_apps.properties.serializers.visit_parts.property_visit_serializer import (
    get_visit_language,
)
from core_apps.advertising.views_parts.language import language as ad_language
from core_apps.features.services.tenancy_invitations_parts.validate_accounts import (
    localized,
)


@pytest.mark.django_db
def test_type_catalog_matches_filter_labels_and_keeps_identifiers():
    prop_type = PropertyType.objects.update_or_create(
        slug="apartment", defaults={"name": "Apartment"}
    )[0]
    client = APIClient()
    labels = {}
    for locale, expected in [("ar", "شقة"), ("en", "Apartment")]:
        response = client.get("/api/v1/properties/types/", HTTP_ACCEPT_LANGUAGE=locale)
        assert response.status_code == 200
        assert response["Content-Language"] == locale
        assert "Accept-Language" in response["Vary"]
        entries = response.json()["data"]
        if isinstance(entries, dict):
            entries = entries["results"]
        item = next(item for item in entries if item["id"] == str(prop_type.id))
        assert item["name"] == expected
        assert item["slug"] == "apartment"
        filters = client.get(
            "/api/v1/properties/filter-options/", HTTP_ACCEPT_LANGUAGE=locale
        ).json()["data"]
        assert (
            next(
                item
                for item in filters["property_types"]
                if item["value"] == "apartment"
            )["label"]
            == expected
        )
        labels[locale] = item
    assert labels["ar"]["id"] == labels["en"]["id"]
    prop_type.refresh_from_db()
    assert prop_type.name == "Apartment"


@pytest.mark.django_db
def test_location_catalog_localizes_names_without_rewriting_database_or_slug():
    gov = Governorate.objects.create(name="Cairo")
    city = City.objects.create(name="6 اكتوبر", governorate=gov)
    client = APIClient()
    for locale, city_name, gov_name in [
        ("ar", "6 أكتوبر", "القاهرة"),
        ("en", "6th of October", "Cairo"),
    ]:
        response = client.get("/api/v1/properties/cities/", HTTP_ACCEPT_LANGUAGE=locale)
        data = response.json()["data"]
        entries = data["results"] if isinstance(data, dict) else data
        item = next(item for item in entries if item["id"] == str(city.id))
        assert item["name"] == city_name
        assert item["governorate_name"] == gov_name
        assert item["slug"] == city.slug
        assert item["governorate"] == str(gov.id)
    city.refresh_from_db()
    assert city.name == "6 اكتوبر"


@pytest.mark.django_db
def test_admin_and_custom_catalog_content_is_preserved():
    custom = PropertyType.objects.create(name="Garden apartment", slug="custom-garden")
    standard = PropertyType.objects.update_or_create(
        slug="apartment", defaults={"name": "Apartment"}
    )[0]
    factory = APIRequestFactory()
    mobile = factory.get("/api/v1/properties/types/", HTTP_ACCEPT_LANGUAGE="ar")
    admin = factory.get("/api/v1/admin/property-types/", HTTP_ACCEPT_LANGUAGE="ar")
    assert (
        PropertyTypeSerializer(custom, context={"request": mobile}).data["name"]
        == custom.name
    )
    assert (
        PropertyTypeSerializer(standard, context={"request": admin}).data["name"]
        == standard.name
    )


@pytest.mark.parametrize(
    "path,header,expected",
    [
        ("/api/v1/properties/filter-options/", "ar;q=0.2,en-US;q=0.9", "en"),
        ("/api/v1/properties/filter-options/?language=ar", "en-US", "ar"),
        ("/api/v1/properties/filter-options/?lang=en", "ar-EG", "en"),
        ("/api/v1/properties/filter-options/", "ar;q=0,en;q=1", "en"),
        ("/api/v1/properties/filter-options/", "", "en"),
    ],
)
@pytest.mark.django_db
def test_catalog_visit_and_advertising_agree_with_negotiated_language(
    path, header, expected
):
    request = APIRequestFactory().get(path, HTTP_ACCEPT_LANGUAGE=header)
    assert get_visit_language(request) == expected
    assert ad_language(request) == expected
    assert localized(request, "English", "عربي") == (
        "عربي" if expected == "ar" else "English"
    )
    response = APIClient().get(path, HTTP_ACCEPT_LANGUAGE=header)
    assert response["Content-Language"] == expected
    label = response.json()["data"]["ordering"][0]["label"]
    assert label == ("الأكثر صلة" if expected == "ar" else "Most relevant")


@pytest.mark.django_db
def test_admin_can_still_edit_the_catalog_source_name():
    item = PropertyType.objects.update_or_create(
        slug="apartment", defaults={"name": "Apartment"}
    )[0]
    request = APIRequestFactory().patch(
        "/api/v1/admin/property-types/", HTTP_ACCEPT_LANGUAGE="ar"
    )
    serializer = PropertyTypeSerializer(
        item,
        data={"name": "Managed apartment"},
        partial=True,
        context={"request": request},
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    item.refresh_from_db()
    assert item.name == "Managed apartment"
