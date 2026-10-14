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
                "district": "Heliopolis",
            },
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
        assert "owner" in data
        assert "is_verified" in data
        assert "owner_is_verified" in data
        assert "is_ownership_verified" in data
        assert data["owner"]["is_verified"] == another_user.is_verified

    def test_owner_availability_supports_week_start_query_param(
        self, auth_client, user, apartment_type
    ):
        from datetime import time, timedelta
        from django.utils import timezone
        from core_apps.properties.models import OwnerAvailabilitySlot

        property_obj = create_property(user, apartment_type)
        target_week_start = timezone.localdate() + timedelta(days=7)
        slot_date = target_week_start + timedelta(days=1)
        OwnerAvailabilitySlot.objects.create(
            owner=user,
            property=property_obj,
            date=slot_date,
            time=time(14, 0),
            is_enabled=True,
        )

        url = reverse("owner-availability-week", kwargs={"property_id": property_obj.id})
        res = auth_client.get(url, {"week_start": target_week_start.isoformat()})
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["week_start"] == target_week_start.isoformat()
        assert len(data["days"]) >= 1
        assert data["days"][0]["date"] == slot_date.isoformat()



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
        visit_date = timezone.localdate() + timedelta(days=2)
        OwnerAvailabilitySlot.objects.create(
            owner=user, property=property_obj, date=visit_date, time="10:00:00"
        )
        OwnerAvailabilitySlot.objects.create(
            owner=user,
            property=property_obj,
            date=visit_date,
            time="11:00:00",
            is_enabled=False,
        )
        OwnerAvailabilitySlot.objects.create(
            owner=user, property=property_obj, date=visit_date, time="12:00:00"
        )
        PropertyVisit.objects.create(
            property=property_obj,
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
        response = api_client.get(
            reverse(
                "property-available-dates",
                kwargs={"property_id": property_obj.id},
            ),
            {"date": visit_date.isoformat()},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"] == {
            "times": [
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
        }

    def test_empty_schedule_and_invalid_requested_date(
        self, api_client, user, apartment_type
    ):
        property_obj = create_property(user, apartment_type)
        url = reverse(
            "property-available-dates", kwargs={"property_id": property_obj.id}
        )

        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"] == {"days": []}

        response = api_client.get(
            url, {"date": (timezone.localdate() + timedelta(days=5)).isoformat()}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_availability_is_isolated_between_an_owners_properties(
        self, api_client, user, apartment_type
    ):
        nasr_city_property = create_property(user, apartment_type)
        other_city_property = create_property(
            user,
            apartment_type,
            title="Different City Property",
            city="Giza",
            district="Dokki",
        )
        visit_date = timezone.localdate() + timedelta(days=2)
        OwnerAvailabilitySlot.objects.create(
            owner=user,
            property=nasr_city_property,
            date=visit_date,
            time="10:00:00",
        )

        response = api_client.get(
            reverse(
                "property-available-dates",
                kwargs={"property_id": other_city_property.id},
            )
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["data"] == {"days": []}

    def test_booking_revalidates_slot_and_prevents_owner_double_booking(
        self, auth_client, api_client, user, another_user, superuser, apartment_type
    ):
        property_obj = create_property(another_user, apartment_type)
        visit_date = timezone.localdate() + timedelta(days=3)
        OwnerAvailabilitySlot.objects.create(
            owner=another_user,
            property=property_obj,
            date=visit_date,
            time="14:00:00",
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
        assert not PropertyVisit.objects.filter(property=property_obj).exists()

    @pytest.mark.parametrize(
        "slot_kind",
        ["disabled", "different_time", "different_date", "different_property", "wrong_owner"],
    )
    def test_booking_requires_matching_enabled_slot(
        self, auth_client, user, another_user, apartment_type, slot_kind
    ):
        property_obj = create_property(another_user, apartment_type)
        visit_date = timezone.localdate() + timedelta(days=3)
        slot_data = {
            "owner": another_user,
            "property": property_obj,
            "date": visit_date,
            "time": "14:00:00",
        }
        if slot_kind == "disabled":
            slot_data["is_enabled"] = False
        elif slot_kind == "different_time":
            slot_data["time"] = "15:00:00"
        elif slot_kind == "different_date":
            slot_data["date"] += timedelta(days=1)
        elif slot_kind == "different_property":
            slot_data["property"] = create_property(another_user, apartment_type)
        else:
            slot_data["owner"] = user
        OwnerAvailabilitySlot.objects.create(**slot_data)

        response = auth_client.post(
            reverse("property-visit-create", kwargs={"property_id": property_obj.id}),
            {"visit_date": visit_date.isoformat(), "visit_time": "14:00:00"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not available" in response.json()["message"]
        assert not PropertyVisit.objects.exists()

    @pytest.mark.parametrize("edit", ["disable", "remove"])
    def test_booking_rechecks_slot_after_availability_was_read(
        self, auth_client, api_client, another_user, apartment_type, edit
    ):
        property_obj = create_property(another_user, apartment_type)
        visit_date = timezone.localdate() + timedelta(days=3)
        slot = OwnerAvailabilitySlot.objects.create(
            owner=another_user,
            property=property_obj,
            date=visit_date,
            time="14:00:00",
        )
        available = api_client.get(
            reverse("property-available-dates", kwargs={"property_id": property_obj.id}),
            {"date": visit_date.isoformat()},
        )
        assert available.status_code == status.HTTP_200_OK
        assert available.json()["data"]["times"][0]["is_available"] is True

        slot.refresh_from_db()
        slots_data = (
            [{"time": slot.time, "is_enabled": False}] if edit == "disable" else []
        )
        PropertyVisitService.replace_property_day_availability(
            property_obj, visit_date, slots_data
        )
        if edit == "disable":
            slot.refresh_from_db()
            assert slot.is_enabled is False
        else:
            assert not property_obj.availability_slots.exists()
        response = auth_client.post(
            reverse("property-visit-create", kwargs={"property_id": property_obj.id}),
            {"visit_date": visit_date.isoformat(), "visit_time": "14:00:00"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not available" in response.json()["message"]
        assert not PropertyVisit.objects.exists()

    def test_confirmed_visit_keeps_slot_unavailable(
        self, auth_client, another_user, superuser, apartment_type
    ):
        property_obj = create_property(another_user, apartment_type)
        visit_date = timezone.localdate() + timedelta(days=3)
        OwnerAvailabilitySlot.objects.create(
            owner=another_user, property=property_obj, date=visit_date, time="14:00:00"
        )
        visit = PropertyVisit.objects.create(
            tenant=superuser,
            property=property_obj,
            visit_date=visit_date,
            visit_time="14:00:00",
            status=PropertyVisit.Status.CONFIRMED,
        )

        response = auth_client.post(
            reverse("property-visit-create", kwargs={"property_id": property_obj.id}),
            {"visit_date": visit_date.isoformat(), "visit_time": "14:00:00"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already booked" in response.json()["message"]
        assert PropertyVisit.objects.get().pk == visit.pk
