import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from core_apps.properties.models import Property, PropertyVisit


def _create_property(owner, property_type, city, governorate, **kwargs):
    defaults = {
        "title": "Apartment in Dokki",
        "description": "Modern apartment walkthrough",
        "price": 8000.00,
        "price_period": Property.PricePeriod.MONTHLY,
        "property_type": property_type,
        "city": city,
        "governorate": governorate,
        "district": "Dokki",
        "status": Property.Status.VERIFIED,
        "is_verified": True,
    }
    defaults.update(kwargs)
    return Property.objects.create(owner=owner, **defaults)


@pytest.mark.django_db
class TestMentorPropertyVideoAndDeepLink:
    def test_create_property_with_video_and_duration(
        self, auth_client, user, apartment_type, cairo_city, cairo_governorate
    ):
        url = reverse("property-create")
        payload = {
            "title": "Luxury Studio with Video Tour",
            "description": "Spacious studio with video tour",
            "price": 10000.00,
            "price_period": "monthly",
            "property_type": apartment_type.slug,
            "governorate": str(cairo_governorate.id),
            "city": str(cairo_city.id),
            "district": "Maadi",
            "bedrooms": 1,
            "bathrooms": 1,
            "area": 75,
            "video_duration": 45,
        }
        res = auth_client.post(url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()["data"]
        assert data["video_duration"] == 45
        assert "property_link" in data
        assert f"/properties/{data['id']}" in data["property_link"]

    def test_create_property_rejects_video_duration_over_60_seconds(
        self, auth_client, user, apartment_type, cairo_city, cairo_governorate
    ):
        url = reverse("property-create")
        payload = {
            "title": "Invalid Video Property",
            "description": "Video exceeds 60 seconds",
            "price": 10000.00,
            "price_period": "monthly",
            "property_type": apartment_type.slug,
            "governorate": str(cairo_governorate.id),
            "city": str(cairo_city.id),
            "district": "Maadi",
            "bedrooms": 1,
            "bathrooms": 1,
            "area": 75,
            "video_duration": 75,
        }
        res = auth_client.post(url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_property_detail_returns_video_and_property_link(
        self, auth_client, user, apartment_type, cairo_city, cairo_governorate
    ):
        prop = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
            video_duration=30,
        )
        url = reverse("property-detail", kwargs={"id": prop.id})
        res = auth_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["video_duration"] == 30
        assert data["property_link"] == f"https://sokoun.app/properties/{prop.id}"


@pytest.mark.django_db
class TestReceivedVisitsScheduledTime:
    def test_received_visits_includes_scheduled_time_and_property_id(
        self, auth_client, user, another_user, apartment_type, cairo_city, cairo_governorate
    ):
        prop = _create_property(
            owner=user,
            property_type=apartment_type,
            city=cairo_city,
            governorate=cairo_governorate,
        )
        future_date = timezone.localdate() + timezone.timedelta(days=3)
        visit = PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=future_date,
            visit_time="14:30:00",
            status=PropertyVisit.Status.PENDING,
        )

        url = reverse("owner-visit-list")
        res = auth_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert len(data["results"]) == 1
        item = data["results"][0]
        assert item["id"] == str(visit.id)
        assert item["property_id"] == str(prop.id)
        assert item["visit_date"] == future_date.isoformat()
        assert item["visit_time"] == "14:30:00"
        assert item["time"] == "2:30 PM"
        assert item["status"] == "pending"
