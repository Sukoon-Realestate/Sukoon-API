from core_apps.common.contract_testing import api_json
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from core_apps.chat.models import Message
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from core_apps.notifications.models import Notification
from core_apps.properties.models import (
    City,
    Governorate,
    Property,
    PropertyType,
    PropertyVisit,
    PropertyVisitReview,
    SavedProperty,
)


def _create_property(owner, **kwargs):
    gov, _ = Governorate.objects.get_or_create(slug="cairo", defaults={"name": "Cairo"})
    city, _ = City.objects.get_or_create(
        slug="nasr-city", defaults={"name": "Nasr City", "governorate": gov}
    )
    prop_type, _ = PropertyType.objects.get_or_create(
        slug="apartment", defaults={"name": "Apartment"}
    )
    defaults = {
        "title": "Apartment in Heliopolis",
        "description": "Lovely flat",
        "price": 9000.00,
        "price_period": Property.PricePeriod.MONTHLY,
        "property_type": prop_type,
        "city": city,
        "governorate": gov,
        "district": "Heliopolis",
        "status": Property.Status.VERIFIED,
        "is_verified": True,
    }
    defaults.update(kwargs)
    return Property.objects.create(owner=owner, **defaults)


@pytest.mark.django_db
class TestUnreadCountsAndMyRates:
    def test_owner_unread_counts(self, auth_client, user, another_user):
        # 1. Create a property owned by user
        prop = _create_property(owner=user)

        # 2. Add pending visit request
        future_date = timezone.localdate() + timezone.timedelta(days=2)
        PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date=future_date,
            visit_time="10:00:00",
            status=PropertyVisit.Status.PENDING,
        )

        # 3. Add unread notification
        Notification.objects.create(
            user=user,
            title="طلب زيارة جديد",
            scope="owner",
            is_read=False,
        )

        # 4. Count actual incoming messages in this owner's workspace.
        convo = get_or_create_direct_conversation(
            user=user, other_user=another_user, workspace="owner"
        )
        convo.participant_set.filter(user=user).update(unread_count=43)
        Message.objects.bulk_create([
            Message(conversation=convo, sender=another_user, sequence=i + 1, content="Unread")
            for i in range(3)
        ])

        url = reverse("owner-unread-counts")
        res = auth_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["visit_requests_count"] == 1
        assert data["unread_notifications_count"] == 1
        assert data["unread_chat_messages_count"] == 3

    def test_tenant_unread_counts(self, auth_client, user, another_user):
        prop = _create_property(owner=another_user)

        # Save property
        SavedProperty.objects.create(user=user, property=prop)

        # Active visit request created by user
        future_date = timezone.localdate() + timezone.timedelta(days=2)
        PropertyVisit.objects.create(
            property=prop,
            tenant=user,
            visit_date=future_date,
            visit_time="11:00:00",
            status=PropertyVisit.Status.PENDING,
        )

        # Unread notification
        Notification.objects.create(
            user=user,
            title="تحديث العقار",
            scope="individual",
            is_read=False,
        )

        url = reverse("tenant-unread-counts")
        res = auth_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["favorites_count"] == 1
        assert data["visit_requests_count"] == 1
        assert data["unread_notifications_count"] == 1
        assert data["unread_chat_messages_count"] == 0

    def test_tenant_my_rates_list(self, auth_client, user, another_user):
        prop = _create_property(owner=another_user)
        past_date = timezone.localdate() - timezone.timedelta(days=5)
        visit = PropertyVisit.objects.create(
            property=prop,
            tenant=user,
            visit_date=past_date,
            visit_time="14:00:00",
            status=PropertyVisit.Status.CONFIRMED,
        )
        review = PropertyVisitReview.objects.create(
            visit=visit,
            overall_rating=5,
            cleanliness_rating=5,
            listing_accuracy_rating=4,
            owner_interaction_rating=5,
            comment="Excellent apartment and great host!",
        )

        url = reverse("tenant-my-rates")
        res = auth_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        data = api_json(res)["data"]
        assert len(data["results"]) == 1
        item = data["results"][0]
        assert item["id"] == str(review.id)
        assert item["property_id"] == str(prop.id)
        assert item["property_title"] == prop.title
        assert item["visit_id"] == str(visit.id)
        assert item["rating"] == 5
        assert item["comment"] == "Excellent apartment and great host!"

    def test_owner_unread_counts_unauthenticated(self, client):
        url = reverse("owner-unread-counts")
        res = client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_tenant_unread_counts_unauthenticated(self, client):
        url = reverse("tenant-unread-counts")
        res = client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_tenant_my_rates_unauthenticated(self, client):
        url = reverse("tenant-my-rates")
        res = client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
