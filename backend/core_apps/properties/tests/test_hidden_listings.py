import uuid
from datetime import timedelta
import pytest
from django.urls import reverse
from django.utils import timezone
from core_apps.properties.models import Property, HiddenListingPreference
from .test_views import _create_published_property

pytestmark = pytest.mark.django_db


def command(client, prop, **fields):
    body = {
        "property_id": str(prop.id),
        "property_revision": prop.review_revision,
        "action": "hide",
        "expected_revision": 0,
        **fields,
    }
    return client.post(
        reverse("hidden-listings"),
        body,
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )


def test_whole_property_hide_restore_expiry_and_account_isolation(
    api_client, user, another_user
):
    prop = _create_published_property(owner=user, price=1000)
    api_client.force_authenticate(user=user)
    hidden = command(api_client, prop)
    assert hidden.status_code == 200
    row = HiddenListingPreference.objects.get(user=user)
    assert timedelta(days=29) < row.expires_at - timezone.now() <= timedelta(days=30)
    assert api_client.get(reverse("property-list")).data["count"] == 0
    assert (
        api_client.get(reverse("property-detail", kwargs={"id": prop.id})).status_code
        == 200
    )
    api_client.force_authenticate(user=another_user)
    assert api_client.get(reverse("property-list")).data["count"] == 1
    assert api_client.get(reverse("hidden-listings")).data["preferences"] == []
    api_client.force_authenticate(user=user)
    restored = command(api_client, prop, action="restore", expected_revision=1)
    assert restored.status_code == 200
    assert api_client.get(reverse("property-list")).data["count"] == 1
    hidden = command(api_client, prop, expected_revision=2, persistent=True)
    assert hidden.data["expires_at"] is None
    HiddenListingPreference.objects.filter(user=user).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert api_client.get(reverse("property-list")).data["count"] == 1


def test_hiding_one_offer_retains_sibling_and_recalculates_price(api_client, user):
    prop = _create_published_property(owner=user, price=1000)
    offers = [
        {
            "id": str(uuid.uuid4()),
            "revision": 1,
            "name": f"Bed {n}",
            "rental_scope": "bed",
            "availability": "available",
            "terms": {"price": str(n * 100), "price_period": "monthly"},
        }
        for n in [1, 2]
    ]
    Property.objects.filter(pk=prop.pk).update(
        rental_inventory={"offers": offers},
        rental_min_price=100,
        rental_price_period="monthly",
    )
    prop.refresh_from_db()
    api_client.force_authenticate(user=user)
    hidden = command(api_client, prop, offer_id=offers[0]["id"], offer_revision=1)
    assert hidden.status_code == 200
    result = api_client.get(reverse("property-list"))
    assert result.data["count"] == 1
    summary = result.data["results"][0]["rental_summary"]
    assert summary["eligible_count"] == 1
    assert summary["price"] == "200.00"
    assert summary["labels"] == ["Bed 2"]


def test_lost_ack_replay_does_not_extend_expiry_or_repeat_write(api_client, user):
    prop = _create_published_property(owner=user, price=1000)
    api_client.force_authenticate(user=user)
    body = {
        "property_id": str(prop.id),
        "property_revision": prop.review_revision,
        "action": "hide",
        "expected_revision": 0,
    }
    key = str(uuid.uuid4())
    first = api_client.post(
        reverse("hidden-listings"), body, format="json", HTTP_IDEMPOTENCY_KEY=key
    )
    second = api_client.post(
        reverse("hidden-listings"), body, format="json", HTTP_IDEMPOTENCY_KEY=key
    )
    assert first.status_code == second.status_code == 200
    assert first.data == second.data
    assert HiddenListingPreference.objects.get(user=user).revision == 1
    assert command(api_client, prop).status_code == 409


def test_stale_listing_revision_cannot_commit_a_new_preference(api_client, user):
    prop = _create_published_property(owner=user, price=1000)
    api_client.force_authenticate(user=user)
    Property.objects.filter(pk=prop.pk).update(review_revision=prop.review_revision + 1)
    assert command(api_client, prop).status_code == 409
    assert not HiddenListingPreference.objects.filter(user=user).exists()


def test_withdrawn_property_details_stay_private_but_preference_can_be_restored(
    api_client, user
):
    prop = _create_published_property(
        owner=user, title="Private after withdrawal", price=1000
    )
    api_client.force_authenticate(user=user)
    assert command(api_client, prop).status_code == 200
    Property.objects.filter(pk=prop.pk).update(status=Property.Status.HIDDEN)
    preferences = api_client.get(reverse("hidden-listings"))
    assert preferences.status_code == 200
    assert preferences.data["preferences"][0]["title"] == ""
    assert (
        command(api_client, prop, action="restore", expected_revision=1).status_code
        == 200
    )
