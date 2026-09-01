from datetime import time, timedelta
import uuid

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from core_apps.properties.models import (
    OwnerAvailabilitySlot,
    Property,
    PropertyRating,
    PropertyVisit,
    PropertyVisitReview,
)


def create_property(owner, apartment_type, cairo_city, cairo_governorate):
    return Property.objects.create(
        owner=owner,
        title="Furnished Apartment",
        price=6500,
        price_period=Property.PricePeriod.MONTHLY,
        property_type=apartment_type,
        bedrooms=3,
        governorate=cairo_governorate,
        city=cairo_city,
        district="Nasr City",
    )


@pytest.mark.django_db
class TestTenantVisitRequestScreens:
    def test_list_returns_card_data_and_status_actions(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        property_obj = create_property(
            another_user, apartment_type, cairo_city, cairo_governorate
        )
        visit = PropertyVisit.objects.create(
            property=property_obj,
            tenant=user,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(14),
            status=PropertyVisit.Status.CONFIRMED,
        )

        response = auth_client.get(reverse("tenant-visit-request-list"))

        assert response.status_code == status.HTTP_200_OK
        card = response.json()["data"]["results"][0]
        assert set(card) == {
            "id",
            "property",
            "owner",
            "day_label",
            "time_label",
            "status_label",
            "actions",
            "alternative_search_filters",
        }
        assert set(card["property"]) == {"id", "title", "location", "price"}
        assert card["id"] == str(visit.id)
        assert card["property"]["title"] == "Furnished Apartment"
        assert card["property"]["location"] == "Nasr City, Cairo"
        assert card["owner"]["name"] == another_user.get_full_name
        assert card["status_label"] == "مقبول"
        assert card["actions"] == {
            "can_cancel": True,
            "can_chat": True,
            "can_review": False,
            "can_find_alternative": False,
        }

    def test_detail_reveals_owner_phone_only_after_confirmation(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        another_user.profile.phone_number = "+201012345432"
        another_user.profile.save()
        property_obj = create_property(
            another_user, apartment_type, cairo_city, cairo_governorate
        )
        visit = PropertyVisit.objects.create(
            property=property_obj,
            tenant=user,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(14),
        )
        url = reverse("tenant-visit-request-detail", kwargs={"id": visit.id})

        pending = auth_client.get(url).json()["data"]
        assert pending["owner"]["phone_number"] == ""

        visit.status = PropertyVisit.Status.CONFIRMED
        visit.save(update_fields=["status"])
        confirmed = auth_client.get(url).json()["data"]
        assert confirmed["owner"]["phone_number"] == "+201012345432"
        assert "*" in confirmed["owner"]["masked_phone_number"]

    def test_other_tenant_cannot_read_or_cancel_visit(
        self,
        api_client,
        user,
        another_user,
        superuser,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        property_obj = create_property(
            another_user, apartment_type, cairo_city, cairo_governorate
        )
        visit = PropertyVisit.objects.create(
            property=property_obj,
            tenant=user,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(14),
        )
        api_client.force_authenticate(superuser)

        detail = api_client.get(
            reverse("tenant-visit-request-detail", kwargs={"id": visit.id})
        )
        cancel = api_client.post(
            reverse("property-visit-cancel", kwargs={"id": visit.id}), {}
        )

        assert detail.status_code == status.HTTP_404_NOT_FOUND
        assert cancel.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestPropertyVisitReviewAPI:
    def test_tenant_reviews_completed_confirmed_visit(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        property_obj = create_property(
            another_user, apartment_type, cairo_city, cairo_governorate
        )
        visit = PropertyVisit.objects.create(
            property=property_obj,
            tenant=user,
            visit_date=timezone.localdate() - timedelta(days=1),
            visit_time=time(14),
            status=PropertyVisit.Status.CONFIRMED,
        )
        payload = {
            "overall_rating": 4,
            "cleanliness_rating": 4,
            "listing_accuracy_rating": 5,
            "owner_interaction_rating": 4,
            "comment": "Matched the listing.",
        }

        response = auth_client.post(
            reverse("property-visit-review-create", kwargs={"id": visit.id}),
            payload,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert PropertyVisitReview.objects.filter(visit=visit).exists()
        assert PropertyRating.objects.get(user=user, property=property_obj).rating == 4

        duplicate = auth_client.post(
            reverse("property-visit-review-create", kwargs={"id": visit.id}),
            payload,
            format="json",
        )
        assert duplicate.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_review_before_visit_and_invalid_scores(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        property_obj = create_property(
            another_user, apartment_type, cairo_city, cairo_governorate
        )
        visit = PropertyVisit.objects.create(
            property=property_obj,
            tenant=user,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(14),
            status=PropertyVisit.Status.CONFIRMED,
        )
        url = reverse("property-visit-review-create", kwargs={"id": visit.id})
        valid_payload = {
            "overall_rating": 4,
            "cleanliness_rating": 4,
            "listing_accuracy_rating": 5,
            "owner_interaction_rating": 4,
        }

        early = auth_client.post(url, valid_payload, format="json")
        invalid = auth_client.post(
            url, {**valid_payload, "cleanliness_rating": 6}, format="json"
        )

        assert early.status_code == status.HTTP_400_BAD_REQUEST
        assert invalid.status_code == status.HTTP_400_BAD_REQUEST

    def test_review_requires_authentication(self, api_client):
        response = api_client.post(
            reverse("property-visit-review-create", kwargs={"id": uuid.uuid4()}),
            {},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestOwnerAvailabilityAndCalendarAPI:
    def test_owner_can_replace_week_slots_but_booked_slot_is_preserved(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        property_obj = create_property(
            user, apartment_type, cairo_city, cairo_governorate
        )
        start_date = timezone.localdate() + timedelta(days=1)
        OwnerAvailabilitySlot.objects.create(
            owner=user, property=property_obj, date=start_date, time=time(9)
        )
        OwnerAvailabilitySlot.objects.create(
            owner=user, property=property_obj, date=start_date, time=time(10)
        )
        OwnerAvailabilitySlot.objects.create(
            owner=user, property=property_obj, date=start_date, time=time(12)
        )
        PropertyVisit.objects.create(
            property=property_obj,
            tenant=another_user,
            visit_date=start_date,
            visit_time=time(10),
        )
        url = reverse(
            "owner-availability-week", kwargs={"property_id": property_obj.id}
        )

        before = auth_client.get(url, {"start_date": start_date.isoformat()})
        assert before.status_code == status.HTTP_200_OK
        slots = before.json()["data"]["days"][0]["slots"]
        assert [slot["time"] for slot in slots] == ["09:00:00", "12:00:00"]

        response = auth_client.put(
            url,
            {
                "availability_date": start_date.isoformat(),
                "slots": [
                    {"time": "09:00:00"},
                    {
                        "time": "11:00:00",
                        "is_enabled": False,
                    },
                ],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        saved_slots = response.json()["data"]["days"][0]["slots"]
        assert [slot["time"] for slot in saved_slots] == ["09:00:00"]
        assert OwnerAvailabilitySlot.objects.filter(
            owner=user, property=property_obj, date=start_date, time=time(10)
        ).exists()
        assert OwnerAvailabilitySlot.objects.filter(
            owner=user,
            property=property_obj,
            date=start_date,
            time=time(11),
            is_enabled=False,
        ).exists()
        assert not OwnerAvailabilitySlot.objects.filter(
            owner=user, property=property_obj, date=start_date, time=time(12)
        ).exists()

    def test_owner_cannot_disable_booked_slot(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        property_obj = create_property(
            user, apartment_type, cairo_city, cairo_governorate
        )
        start_date = timezone.localdate() + timedelta(days=1)
        OwnerAvailabilitySlot.objects.create(
            owner=user, property=property_obj, date=start_date, time=time(10)
        )
        PropertyVisit.objects.create(
            property=property_obj,
            tenant=another_user,
            visit_date=start_date,
            visit_time=time(10),
        )

        response = auth_client.put(
            reverse("owner-availability-week", kwargs={"property_id": property_obj.id}),
            {
                "availability_date": start_date.isoformat(),
                "slots": [
                    {
                        "time": "10:00:00",
                        "is_enabled": False,
                    }
                ],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Booked visit slots cannot be disabled" in response.json()["message"]

    def test_availability_list_omits_days_without_bookable_slots(
        self,
        auth_client,
        user,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        property_obj = create_property(
            user, apartment_type, cairo_city, cairo_governorate
        )
        start_date = timezone.localdate() + timedelta(days=1)
        disabled_date = start_date + timedelta(days=1)
        booked_date = start_date + timedelta(days=2)
        OwnerAvailabilitySlot.objects.create(
            owner=user, property=property_obj, date=start_date, time=time(9)
        )
        OwnerAvailabilitySlot.objects.create(
            owner=user,
            property=property_obj,
            date=disabled_date,
            time=time(9),
            is_enabled=False,
        )
        OwnerAvailabilitySlot.objects.create(
            owner=user, property=property_obj, date=booked_date, time=time(9)
        )
        PropertyVisit.objects.create(
            property=property_obj,
            tenant=another_user,
            visit_date=booked_date,
            visit_time=time(9),
        )

        response = auth_client.get(
            reverse("owner-availability-week", kwargs={"property_id": property_obj.id}),
            {"start_date": start_date.isoformat()},
        )

        assert response.status_code == status.HTTP_200_OK
        assert [day["date"] for day in response.json()["data"]["days"]] == [
            start_date.isoformat()
        ]

    def test_calendar_returns_month_indicators_and_selected_day_visits(
        self,
        auth_client,
        user,
        another_user,
        superuser,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        property_obj = create_property(
            user, apartment_type, cairo_city, cairo_governorate
        )
        selected_date = timezone.localdate() + timedelta(days=3)
        PropertyVisit.objects.create(
            property=property_obj,
            tenant=another_user,
            visit_date=selected_date,
            visit_time=time(15),
            status=PropertyVisit.Status.CONFIRMED,
        )
        PropertyVisit.objects.create(
            property=property_obj,
            tenant=superuser,
            visit_date=selected_date,
            visit_time=time(17, 30),
            status=PropertyVisit.Status.PENDING,
        )
        response = auth_client.get(
            reverse("owner-visit-calendar"),
            {
                "year": selected_date.year,
                "month": selected_date.month,
                "date": selected_date.isoformat(),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["selected_date"] == selected_date.isoformat()
        assert data["days"] == [
            {
                "date": selected_date.isoformat(),
                "day": selected_date.day,
                "visit_count": 2,
            }
        ]
        assert [visit["tenant"]["name"] for visit in data["visits"]] == [
            another_user.get_full_name,
            superuser.get_full_name,
        ]

    def test_owner_availability_and_calendar_require_authentication(self, api_client):
        availability = api_client.get(
            reverse("owner-availability-week", kwargs={"property_id": uuid.uuid4()})
        )
        calendar = api_client.get(
            reverse("owner-visit-calendar"), {"year": 2026, "month": 9}
        )
        assert availability.status_code == status.HTTP_401_UNAUTHORIZED
        assert calendar.status_code == status.HTTP_401_UNAUTHORIZED
