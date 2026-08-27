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


def create_property(owner, property_type, **kwargs):
    defaults = {
        "title": "Mobile API Property",
        "price": 12000,
        "city": "Cairo",
        "district": "Maadi",
        "status": Property.Status.VERIFIED,
    }
    defaults.update(kwargs)
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
            {"country": "Egypt", "city": "Cairo", "district": "Heliopolis"},
            {"country": "Egypt", "city": "Cairo", "district": "Maadi"},
            {"country": "Egypt", "city": "Cairo", "district": "Nasr City"},
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

    def test_requires_authentication(self, api_client, apartment_type):
        response = api_client.get(
            reverse("property-available-places"),
            {"property_type_id": apartment_type.id},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


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
        assert data["rating"] == 4.5
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
        assert data["rating"] == 0.0


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


@pytest.mark.django_db
class TestAvailableDatesAndBooking:
    def test_returns_owner_schedule_and_marks_disabled_and_booked_slots(
        self, api_client, user, another_user, apartment_type
    ):
        property_obj = create_property(user, apartment_type)
        other_property = create_property(
            user, apartment_type, title="Owner's other property"
        )
        visit_date = timezone.localdate() + timedelta(days=2)
        OwnerAvailabilitySlot.objects.create(
            owner=user, date=visit_date, time="10:00:00"
        )
        OwnerAvailabilitySlot.objects.create(
            owner=user, date=visit_date, time="11:00:00", is_enabled=False
        )
        OwnerAvailabilitySlot.objects.create(
            owner=user, date=visit_date, time="12:00:00"
        )
        PropertyVisit.objects.create(
            property=other_property,
            tenant=another_user,
            visit_date=visit_date,
            visit_time="12:00:00",
        )

        response = api_client.get(
            reverse(
                "property-available-dates",
                kwargs={"property_id": property_obj.id},
            )
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["days"] == [
            {
                "day": visit_date.strftime("%A").lower(),
                "date": f"{visit_date.day}/{visit_date.month}",
                "visit_date": visit_date.isoformat(),
            }
        ]
        assert data["times"] == [
            {
                "time": "10:00 AM",
                "visit_time": "10:00:00",
                "is_available": True,
            },
            {
                "time": "11:00 AM",
                "visit_time": "11:00:00",
                "is_available": False,
            },
            {
                "time": "12:00 PM",
                "visit_time": "12:00:00",
                "is_available": False,
            },
        ]

    def test_empty_schedule_and_invalid_requested_date(
        self, api_client, user, apartment_type
    ):
        property_obj = create_property(user, apartment_type)
        url = reverse(
            "property-available-dates", kwargs={"property_id": property_obj.id}
        )

        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"] == {"days": [], "times": []}

        response = api_client.get(
            url, {"date": (timezone.localdate() + timedelta(days=5)).isoformat()}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_booking_revalidates_slot_and_prevents_owner_double_booking(
        self, auth_client, api_client, user, another_user, superuser, apartment_type
    ):
        property_obj = create_property(another_user, apartment_type)
        visit_date = timezone.localdate() + timedelta(days=3)
        OwnerAvailabilitySlot.objects.create(
            owner=another_user, date=visit_date, time="14:00:00"
        )
        url = reverse("property-visit-create", kwargs={"property_id": property_obj.id})
        payload = {
            "visit_date": visit_date.isoformat(),
            "visit_time": "14:00:00",
        }

        first_response = auth_client.post(url, payload)
        assert first_response.status_code == status.HTTP_201_CREATED

        api_client.force_authenticate(user=superuser)
        second_response = api_client.post(url, payload)
        assert second_response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already booked" in second_response.json()["message"]

    def test_booking_rejects_unconfigured_slot(
        self, auth_client, another_user, apartment_type
    ):
        property_obj = create_property(another_user, apartment_type)
        visit_date = timezone.localdate() + timedelta(days=3)
        response = auth_client.post(
            reverse("property-visit-create", kwargs={"property_id": property_obj.id}),
            {"visit_date": visit_date.isoformat(), "visit_time": "09:00:00"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not available" in response.json()["message"]
