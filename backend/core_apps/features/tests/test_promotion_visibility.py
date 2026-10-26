from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from core_apps.admin_api.tests.test_analytics_periods import home  # noqa: F401
from core_apps.features.models import BoostCampaign, RentInvoice
from core_apps.properties.models import Property
from core_apps.properties.views.property_parts.property_list_apiview import (
    PropertyListAPIView,
    PropertyNewListAPIView,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("view", [PropertyListAPIView, PropertyNewListAPIView])
def test_public_feed_uses_request_time_after_worker_started(view, home):  # noqa: F811
    home.status = Property.Status.VERIFIED
    home.is_verified = True
    home.save()
    now = timezone.now()
    campaign = BoostCampaign.objects.create(
        owner=home.owner,
        property=home,
        option_id="local-visibility",
        duration_days=1,
        starts_at=now,
        ends_at=now + timedelta(days=1),
        status="active",
    )

    def sponsored():
        response = view.as_view()(APIRequestFactory().get("/api/v1/properties/"))
        assert response.status_code == 200
        row = next(
            row for row in response.data["results"] if str(row["id"]) == str(home.id)
        )
        return row["is_sponsored"]

    assert sponsored() is True
    # No restart or expiration task: the same imported view must see the end.
    campaign.ends_at = timezone.now()
    campaign.save(update_fields=["ends_at"])
    assert sponsored() is False
    campaign.starts_at = timezone.now() + timedelta(days=1)
    campaign.ends_at = campaign.starts_at + timedelta(days=1)
    campaign.save(update_fields=["starts_at", "ends_at"])
    assert sponsored() is False


@pytest.mark.parametrize(
    "status", ["active", "paused", "pending", "cancelled", "failed", "completed"]
)
def test_owner_reads_expiry_without_rewriting_pending_purchase(
    status, home, api_client  # noqa: F811
):
    now = timezone.now()
    campaign = BoostCampaign.objects.create(
        owner=home.owner,
        property=home,
        option_id="local-expiry",
        duration_days=1,
        starts_at=now - timedelta(days=2),
        ends_at=now - timedelta(days=1),
        status=status,
    )
    api_client.force_authenticate(home.owner)
    response = api_client.get("/api/v1/features/v1/boost-campaigns/")
    assert response.status_code == 200
    expected = "expired" if status in {"active", "paused"} else status
    row = next(
        row for row in response.data["results"] if str(row["id"]) == str(campaign.id)
    )
    assert row["status"] == expected
    campaign.refresh_from_db()
    assert campaign.status == status
    assert not RentInvoice.objects.exists()
