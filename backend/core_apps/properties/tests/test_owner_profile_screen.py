from datetime import date, time
import pytest
from django.urls import reverse
from rest_framework import status

from core_apps.properties.models import (
    City,
    Governorate,
    Property,
    PropertyType,
    PropertyVisit,
    PropertyVisitReview,
)

OWNER_PROFILE_URL = reverse("owner-profile")


def create_test_property(owner, title="شقة مدينة نصر"):
    governorate, _ = Governorate.objects.get_or_create(
        slug="cairo", defaults={"name": "Cairo"}
    )
    city, _ = City.objects.get_or_create(
        governorate=governorate,
        slug="nasr-city",
        defaults={"name": "Nasr City"},
    )
    property_type, _ = PropertyType.objects.get_or_create(
        slug="apartment", defaults={"name": "Apartment"}
    )
    return Property.objects.create(
        owner=owner,
        title=title,
        price=6500,
        bedrooms=2,
        bathrooms=1,
        area=90,
        district="مدينة نصر",
        governorate=governorate,
        city=city,
        property_type=property_type,
    )


@pytest.mark.django_db
class TestOwnerProfileScreenAPI:
    """Tests for Owner Profile screen ('ملفي الشخصي')."""

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(OWNER_PROFILE_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_owner_profile_happy_path(self, auth_client, user, another_user):
        user.first_name = "أحمد"
        user.last_name = "محمد علي"
        user.is_verified = True
        user.date_joined = date(2025, 1, 15)
        user.save()
        user.profile.phone_number = "+201012345432"
        user.profile.save()

        # Create 3 properties for this owner (matching "3 عقارات")
        prop1 = create_test_property(user, title="شقة فاخرة")
        prop2 = create_test_property(user, title="فيلا التجمع")
        prop3 = create_test_property(user, title="استوديو المعادي")

        # Create visits and reviews (matching "آخر التقييمات")
        visit1 = PropertyVisit.objects.create(
            tenant=another_user,
            property=prop1,
            visit_date=date(2026, 7, 20),
            visit_time=time(14, 0),
            status=PropertyVisit.Status.CONFIRMED,
        )
        PropertyVisitReview.objects.create(
            visit=visit1,
            overall_rating=5,
            cleanliness_rating=5,
            listing_accuracy_rating=5,
            owner_interaction_rating=5,
            comment="مالك ممتاز ومتعاون جداً",
        )

        res = auth_client.get(OWNER_PROFILE_URL)
        assert res.status_code == status.HTTP_200_OK

        data = res.json()["data"]

        # Owner header assertions
        owner_data = data["owner"]
        assert owner_data["full_name"] == "أحمد محمد علي"
        assert owner_data["is_verified"] is True
        assert owner_data["role_badge"] == "مالك موثّق"
        assert "عضو منذ" in owner_data["member_since_label"]
        assert owner_data["reviews_count"] == 1
        assert owner_data["average_rating"] == 5.0
        assert "5.0 (1 تقييم)" in owner_data["rating_label"]

        # Stats assertions (3 properties, reviews, acceptance rate)
        stats = data["stats"]
        assert stats["properties_count"] == 3
        assert stats["properties_label"] == "عقارات"
        assert stats["reviews_count"] == 1
        assert stats["reviews_label"] == "تقييم"
        assert stats["acceptance_rate"] == 100
        assert stats["acceptance_label"] == "قبول"

        # Account details assertions
        account = data["account_details"]
        assert account["name"] == "أحمد محمد علي"
        assert account["email"] == user.email
        assert account["masked_phone_number"] == "010****432"

        # Privacy notice
        assert (
            data["privacy_notice"]["text"]
            == "رقمك لا يُعرض للمستأجرين – يظهر فقط بعد قبول الزيارة"
        )

        # Recent reviews
        reviews = data["recent_reviews"]
        assert len(reviews) == 1
        assert reviews[0]["reviewer_name"] == another_user.get_full_name
        assert reviews[0]["rating"] == 5
        assert reviews[0]["comment"] == "مالك ممتاز ومتعاون جداً"

    def test_owner_profile_unverified_owner_role_badge(self, auth_client, user):
        user.is_verified = False
        user.save()

        res = auth_client.get(OWNER_PROFILE_URL)
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["data"]["owner"]["role_badge"] == "مالك"

    def test_acceptance_rate_calculation(self, auth_client, user, another_user):
        prop = create_test_property(user)

        # 24 confirmed visits
        for i in range(24):
            PropertyVisit.objects.create(
                tenant=another_user,
                property=prop,
                visit_date=date(2026, 7, 1 + i % 25),
                visit_time=time(10, 0),
                status=PropertyVisit.Status.CONFIRMED,
            )

        # 1 rejected visit
        PropertyVisit.objects.create(
            tenant=another_user,
            property=prop,
            visit_date=date(2026, 7, 28),
            visit_time=time(11, 0),
            status=PropertyVisit.Status.REJECTED,
        )

        # 24 / 25 = 96%
        res = auth_client.get(OWNER_PROFILE_URL)
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["data"]["stats"]["acceptance_rate"] == 96
        assert res.json()["data"]["stats"]["formatted_acceptance_rate"] == "96%"
