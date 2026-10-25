from core_apps.common.contract_testing import api_json
from datetime import date, time, timedelta
import uuid

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
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

        response = auth_client.get(reverse("tenant-visit-request-list"), HTTP_ACCEPT_LANGUAGE="ar")

        assert response.status_code == status.HTTP_200_OK
        card = api_json(response)["data"]["results"][0]
        assert set(card) == {
            "id",
            "property",
            "owner",
            "status",
            "note",
            "created_at",
            "status_label",
            "actions",
            "alternative_search_filters",
            "revision",
            "offer_id",
            "offer_snapshot",
            "post_visit_decision",
            "post_visit_actions",
            "rental_continuation",
            "stay_preferences",
            "viewing_context",
        }
        assert card["stay_preferences"] is None
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
        assert confirmed["owner"]["phone_number"] == ""
        assert confirmed["owner"]["masked_phone_number"] == ""
        assert confirmed["owner"]["is_phone_revealed"] is False
        assert confirmed["owner"]["phone_notice"] == ""

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
    def test_legacy_visit_write_requires_final_confirmation_client(
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

        # The legacy route has no explicit overall score/final confirmation.
        assert response.status_code == status.HTTP_409_CONFLICT
        assert not PropertyVisitReview.objects.filter(visit=visit).exists()
        assert not PropertyRating.objects.filter(
            user=user, property=property_obj
        ).exists()

    def test_legacy_review_retries_do_not_create_rows(
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
        url = reverse("property-visit-review-create", kwargs={"id": visit.id})
        payload = {
            "cleanliness_rating": 5,
            "listing_accuracy_rating": 4,
            "owner_interaction_rating": 5,
            "comment": "Safe retry",
        }
        headers = {"HTTP_IDEMPOTENCY_KEY": "review-1"}

        first = auth_client.post(url, payload, format="json", **headers)
        replay = auth_client.post(url, payload, format="json", **headers)
        changed = auth_client.post(
            url, {**payload, "comment": "Changed"}, format="json", **headers
        )

        assert first.status_code == status.HTTP_409_CONFLICT
        assert replay.status_code == status.HTTP_409_CONFLICT
        assert changed.status_code == status.HTTP_409_CONFLICT
        assert not PropertyVisitReview.objects.filter(visit=visit).exists()

    def test_legacy_criteria_cannot_infer_an_overall_score(
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
        # ? (5 + 5 + 4) / 3 = 4.67 -> rounded to 5
        payload = {
            "cleanliness_rating": 5,
            "listing_accuracy_rating": 5,
            "owner_interaction_rating": 4,
        }
        response = auth_client.post(
            reverse("property-visit-review-create", kwargs={"id": visit.id}),
            payload,
            format="json",
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        assert not PropertyVisitReview.objects.filter(visit=visit).exists()

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
            "cleanliness_rating": 4,
            "listing_accuracy_rating": 5,
            "owner_interaction_rating": 4,
        }

        early = auth_client.post(url, valid_payload, format="json")
        invalid = auth_client.post(
            url, {**valid_payload, "cleanliness_rating": 6}, format="json"
        )

        assert early.status_code == status.HTTP_409_CONFLICT
        assert invalid.status_code == status.HTTP_400_BAD_REQUEST

    def test_review_requires_authentication(self, api_client):
        response = api_client.post(
            reverse("property-visit-review-create", kwargs={"id": uuid.uuid4()}),
            {},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED




@pytest.mark.django_db
class TestPropertyReviewListAPI:
    def test_list_reviews_happy_path_with_summary(
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
        # First visit and review by user
        visit1 = PropertyVisit.objects.create(
            property=property_obj,
            tenant=user,
            visit_date=timezone.localdate() - timedelta(days=2),
            visit_time=time(10),
            status=PropertyVisit.Status.CONFIRMED,
        )
        PropertyVisitReview.objects.create(
            visit=visit1,
            overall_rating=5,
            cleanliness_rating=5,
            listing_accuracy_rating=5,
            owner_interaction_rating=4,
            comment="Great apartment, very clean!",
        )

        # Second visit and review by superuser
        visit2 = PropertyVisit.objects.create(
            property=property_obj,
            tenant=superuser,
            visit_date=timezone.localdate() - timedelta(days=1),
            visit_time=time(14),
            status=PropertyVisit.Status.CONFIRMED,
        )
        PropertyVisitReview.objects.create(
            visit=visit2,
            overall_rating=4,
            cleanliness_rating=4,
            listing_accuracy_rating=4,
            owner_interaction_rating=4,
            comment="Nice host and decent place.",
        )

        url = reverse("property-review-list", kwargs={"property_id": property_obj.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]

        # Verify summary
        summary = data["summary"]
        assert summary == {
            "total_reviews": 0,
            "average_rating": None,
            "context_type": "viewing",
        }

        # Verify results
        results = data["results"]
        assert len(results) == 2
        # Most recent first
        assert results[0]["comment"] == "Nice host and decent place."
        assert results[0]["reviewer"]["name"] == ""
        assert results[0]["verification_basis"] == "legacy_unverified"
        assert results[0]["overall_rating"] == 4

        assert results[1]["comment"] == "Great apartment, very clean!"
        assert results[1]["reviewer"]["name"] == ""
        assert results[1]["overall_rating"] == 5

    def test_list_reviews_empty(
        self,
        api_client,
        another_user,
        apartment_type,
        cairo_city,
        cairo_governorate,
    ):
        property_obj = create_property(
            another_user, apartment_type, cairo_city, cairo_governorate
        )
        url = reverse("property-review-list", kwargs={"property_id": property_obj.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["summary"] == {
            "total_reviews": 0,
            "average_rating": None,
            "context_type": "viewing",
        }
        assert data["results"] == []

    def test_list_reviews_property_not_found(self, api_client):
        url = reverse("property-review-list", kwargs={"property_id": uuid.uuid4()})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_reviews_query_count(
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
        for i, reviewer in enumerate([user, superuser]):
            visit = PropertyVisit.objects.create(
                property=property_obj,
                tenant=reviewer,
                visit_date=timezone.localdate() - timedelta(days=i + 1),
                visit_time=time(11),
                status=PropertyVisit.Status.CONFIRMED,
            )
            PropertyVisitReview.objects.create(
                visit=visit,
                overall_rating=4,
                cleanliness_rating=4,
                listing_accuracy_rating=4,
                owner_interaction_rating=4,
            )

        url = reverse("property-review-list", kwargs={"property_id": property_obj.id})
        with CaptureQueriesContext(connection) as ctx:
            response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Queries: 1 get property, 1 aggregates, 1 count for pagination, 1 select reviews with tenant/profile
        assert len(ctx.captured_queries) <= 5


class TestBilingualVisitLabels:
    """Verifies BE003: English and Arabic visit requests and calendar labels."""

    def test_tenant_visit_request_labels_in_english_and_arabic(
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
        custom_note = "Please ensure someone is available at 2 PM sharp."
        visit = PropertyVisit.objects.create(
            property=property_obj,
            tenant=user,
            visit_date=timezone.localdate() + timedelta(days=1),
            visit_time=time(14, 30),
            status=PropertyVisit.Status.CONFIRMED,
            note=custom_note,
        )

        # English request
        res_en = auth_client.get(
            reverse("tenant-visit-request-list"),
            HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9",
        )
        assert res_en.status_code == status.HTTP_200_OK
        assert res_en.headers.get("Content-Language") == "en"
        card_en = api_json(res_en)["data"]["results"][0]
        assert card_en["status_label"] == "Accepted"
        # Free-text detail preservation
        detail_res_en = auth_client.get(
            reverse("tenant-visit-request-detail", kwargs={"id": visit.id}),
            HTTP_ACCEPT_LANGUAGE="en",
        )
        assert detail_res_en.status_code == status.HTTP_200_OK
        assert api_json(detail_res_en)["data"]["note"] == custom_note

        # Arabic request
        res_ar = auth_client.get(
            reverse("tenant-visit-request-list"),
            HTTP_ACCEPT_LANGUAGE="ar-EG,ar;q=0.9",
        )
        assert res_ar.status_code == status.HTTP_200_OK
        assert res_ar.headers.get("Content-Language") == "ar"
        card_ar = api_json(res_ar)["data"]["results"][0]
        assert card_ar["status_label"] == "مقبول"
        detail_res_ar = auth_client.get(
            reverse("tenant-visit-request-detail", kwargs={"id": visit.id}),
            HTTP_ACCEPT_LANGUAGE="ar",
        )
        assert detail_res_ar.status_code == status.HTTP_200_OK
        assert api_json(detail_res_ar)["data"]["note"] == custom_note
