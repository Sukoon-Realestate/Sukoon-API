from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from core_apps.properties.models import (
    OwnerAvailabilitySlot,
    Property,
    PropertyFavorite,
    PropertyRating,
    PropertyType,
    PropertyVisit,
    SavedProperty,
)
from core_apps.properties.services import PropertyVisitService


def create_property(owner, property_type, **kwargs):
    from core_apps.properties.models import City, Governorate

    defaults = {
        "title": "Mobile API Property",
        "price": 12000,
        "city": "Cairo",
        "district": "Maadi",
        "status": Property.Status.VERIFIED,
    }
    defaults.update(kwargs)
    city_name = defaults.pop("city", "Cairo")
    governorate = Governorate.objects.get_or_create(
        slug="cairo", defaults={"name": "Cairo"}
    )[0]
    defaults["city"] = City.objects.get_or_create(
        governorate=governorate,
        slug=city_name.lower().replace(" ", "-"),
        defaults={"name": city_name},
    )[0]
    defaults["governorate"] = governorate
    return Property.objects.create(owner=owner, property_type=property_type, **defaults)


@pytest.mark.django_db
class TestAvailablePlaces:
    def test_returns_distinct_approved_locations_for_property_type(
        self, auth_client, user, apartment_type
    ):
        create_property(user, apartment_type)
        create_property(user, apartment_type, title="Duplicate location")
        create_property(
            user,
            apartment_type,
            title="Nasr City property",
            district="Nasr City",
        )
        create_property(
            user,
            apartment_type,
            title="Legacy approved property",
            district="Heliopolis",
            status=Property.Status.UNDER_REVIEW,
            is_verified=True,
        )
        create_property(
            user,
            apartment_type,
            title="Not approved",
            district="Hidden",
            status=Property.Status.UNDER_REVIEW,
        )
        villa_type = PropertyType.objects.get(slug="villa")
        create_property(user, villa_type, title="Different type", district="Zamalek")

        response = auth_client.get(
            reverse("property-available-places"),
            {"property_type_id": apartment_type.id},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["places"] == [
            {
                "governorate": "Cairo",
                "city": "Cairo",
                "district": "Maadi",
            },
            {
                "governorate": "Cairo",
                "city": "Cairo",
                "district": "Nasr City",
            },
        ]

    def test_valid_type_without_properties_returns_empty_array(
        self, auth_client, apartment_type
    ):
        response = auth_client.get(
            reverse("property-available-places"),
            {"property_type_id": apartment_type.id},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"]["places"] == []

    @pytest.mark.parametrize("params", [{}, {"property_type_id": "not-a-uuid"}])
    def test_missing_or_invalid_property_type_returns_400(self, auth_client, params):
        response = auth_client.get(reverse("property-available-places"), params)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_public_guest_access_allowed(self, api_client, apartment_type):
        response = api_client.get(
            reverse("property-available-places"),
            {"property_type_id": apartment_type.id},
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestPropertyDetailsMobileFields:
    def test_authenticated_details_include_amenities_engagement_and_rating(
        self, auth_client, user, another_user, apartment_type
    ):
        property_obj = create_property(
            another_user,
            apartment_type,
            has_wifi=True,
            has_garage=True,
            has_water_meter=False,
            is_furnished=True,
        )
        PropertyFavorite.objects.create(user=user, property=property_obj)
        SavedProperty.objects.create(user=user, property=property_obj)
        PropertyRating.objects.create(user=user, property=property_obj, rating=4)
        PropertyRating.objects.create(
            user=another_user, property=property_obj, rating=5
        )

        response = auth_client.get(
            reverse("property-detail", kwargs={"id": property_obj.id})
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["amenities"] == ["wifi", "garage"]
        assert data["is_fav"] is True
        assert data["is_saved"] is True
        assert data["rating"] is None  # Legacy ratings lack a verified F66 experience.
        assert data["is_furnished"] is True
        for field in PropertyDetailAmenityFields.MODEL_FIELDS:
            assert field not in data

    def test_anonymous_details_use_stable_false_and_numeric_defaults(
        self, api_client, another_user, apartment_type
    ):
        property_obj = create_property(another_user, apartment_type)
        response = api_client.get(
            reverse("property-detail", kwargs={"id": property_obj.id})
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["amenities"] == []
        assert data["is_fav"] is False
        assert data["is_saved"] is False
        assert data["rating"] is None  # No verified experience is not a zero rating.
        assert "owner" in data
        assert "is_verified" in data
        assert "owner_is_verified" in data
        assert "is_ownership_verified" in data
        assert data["owner"]["is_verified"] == another_user.is_verified


class PropertyDetailAmenityFields:
    MODEL_FIELDS = (
        "has_wifi",
        "has_elevator",
        "has_garage",
        "has_security",
        "has_balcony",
        "has_air_conditioning",
        "near_metro",
        "has_natural_gas",
        "has_electricity_meter",
        "has_water_meter",
    )
