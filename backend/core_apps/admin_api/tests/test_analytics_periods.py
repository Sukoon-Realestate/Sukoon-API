"""Analytics must count the named event, within one bounded reporting period."""

from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils import timezone

from core_apps.admin_api.models import StaffProfile, KYCSubmission, UserReport
from core_apps.admin_api.services.analytics_service import get_analytics_stats
from core_apps.admin_api.services.dashboard_service import get_dashboard_overview_stats
from core_apps.admin_api.services.dashboard_service import get_executive_dashboard_stats
from core_apps.properties.models import (
    City,
    Governorate,
    Property,
    PropertyType,
    PropertyVisit,
    PropertyVisitDecision,
)
from core_apps.properties.models.visit import PropertyVisitReview

pytestmark = pytest.mark.django_db


@pytest.fixture
def home(user):
    region = Governorate.objects.create(name="Analytics region")
    return Property.objects.create(
        owner=user,
        title="Analytics home",
        district="With visits",
        governorate=region,
        city=City.objects.create(name="Analytics city", governorate=region),
        property_type=PropertyType.objects.create(
            name="Analytics apartment", slug="analytics-apartment"
        ),
    )


def visit_at(home, tenant, at):
    visit = PropertyVisit.objects.create(property=home, tenant=tenant)
    PropertyVisit.objects.filter(pk=visit.pk).update(created_at=at)
    return visit


def decision_at(visit, tenant, at):
    decision = PropertyVisitDecision.objects.create(
        visit=visit,
        tenant=tenant,
        owner=visit.property.owner,
        value="proceed",
        attended=True,
        attested_at=at,
        visit_revision=visit.revision,
        request_key=uuid4(),
        property_id_snapshot=visit.property.id,
    )
    PropertyVisitDecision.objects.filter(pk=decision.pk).update(created_at=at)


@pytest.mark.parametrize("days", [7, 30, 90])
def test_totals_chart_regions_and_ratings_use_same_exclusive_cutoff(
    home, another_user, days
):
    now = timezone.now()
    start = now - timedelta(days=days)
    # The property itself predates the report: demand counts visits, not listings.
    Property.objects.filter(pk=home.pk).update(created_at=start - timedelta(days=30))
    excluded_old = visit_at(home, another_user, start - timedelta(microseconds=1))
    at_start = visit_at(home, another_user, start)
    recent = visit_at(home, another_user, now - timedelta(microseconds=1))
    visit_at(home, another_user, now)
    visit_at(home, another_user, now + timedelta(days=2))
    decision_at(excluded_old, another_user, now - timedelta(hours=1))
    decision_at(at_start, another_user, now - timedelta(hours=1))
    # Multiple participants do not double-count the completed visit.
    decision_at(at_start, home.owner, now - timedelta(minutes=1))
    decision_at(recent, another_user, now + timedelta(seconds=1))
    for visit, rating, created_at in [(excluded_old, 5, start), (recent, 1, now)]:
        review = PropertyVisitReview.objects.create(
            visit=visit,
            overall_rating=rating,
            cleanliness_rating=rating,
            listing_accuracy_rating=rating,
            owner_interaction_rating=rating,
        )
        PropertyVisitReview.objects.filter(pk=review.pk).update(created_at=created_at)
    with patch(
        "core_apps.admin_api.services.analytics_service.timezone.now", return_value=now
    ):
        data = get_analytics_stats(days)
    assert data["visitRequests"] == "2"
    assert data["completedVisits"] == "1"
    assert sum(row["value"] for row in data["dailyChart"]) == 2
    assert len(data["dailyChart"]) == days
    assert data["dailyChart"][0]["from"] == start.isoformat()
    assert data["dailyChart"][-1]["through"] == now.isoformat()
    assert data["topRegions"] == [{"name": "With visits", "count": 2}]
    assert data["avgRating"] == "5.0 ★"
    assert data["period"] == {
        "days": days,
        "from": start.isoformat(),
        "through": now.isoformat(),
    }


def test_no_visit_region_does_not_create_demand_and_status_does_not_claim_availability(
    home,
):
    Property.objects.filter(pk=home.pk).update(
        status="verified", moderation_blocked=True
    )
    data = get_analytics_stats(7)
    assert data["topRegions"] == []
    assert data["avgRating"] == "غير متاح"
    assert (
        next(row for row in data["propertyActivity"] if row["label"] == "معتمد")[
            "count"
        ]
        == 1
    )
    metric = next(
        row
        for row in get_dashboard_overview_stats()["metrics"]
        if row["icon"] == "building"
    )
    assert metric["title"] == "إجمالي العقارات" and metric["value"] == "1"


@pytest.mark.parametrize(
    "period", ["0", "-1", "1", "365", "99999999999999999", "", "today", "7.0", "07"]
)
def test_unsupported_period_rejected_before_querying(api_client, superuser, period):
    api_client.force_authenticate(superuser)
    with patch("core_apps.admin_api.views.analytics.get_analytics_stats") as compute:
        response = api_client.get(reverse("admin-analytics-stats"), {"period": period})
    assert response.status_code == 400
    compute.assert_not_called()


@pytest.mark.parametrize("period", ["7", "30", "90", None])
def test_supported_period_returns_real_empty_data(api_client, superuser, period):
    api_client.force_authenticate(superuser)
    response = api_client.get(
        reverse("admin-analytics-stats"), {} if period is None else {"period": period}
    )
    assert response.status_code == 200
    assert response.data["period"]["days"] == int(period or "30")
    assert response.data["visitRequests"] == "0"
    assert all(row["value"] == 0 for row in response.data["dailyChart"])


def test_current_authority_required_even_when_request_user_has_cached_profile(
    api_client, user
):
    profile = StaffProfile.objects.create(user=user, role_name="main_admin")
    api_client.force_authenticate(user)
    assert api_client.get(reverse("admin-analytics-stats")).status_code == 200
    StaffProfile.objects.filter(pk=profile.pk).update(is_active=False)
    assert api_client.get(reverse("admin-analytics-stats")).status_code == 403


def test_analytics_denies_ordinary_users_and_anonymous_requests(api_client, user):
    assert api_client.get(reverse("admin-analytics-stats")).status_code == 401
    api_client.force_authenticate(user)
    assert api_client.get(reverse("admin-analytics-stats")).status_code == 403


def test_executive_cutoff_pending_queue_and_status_labels_are_consistent(
    home, another_user
):
    now = timezone.now().replace(hour=12, minute=0, second=0, microsecond=0)
    later = now + timedelta(minutes=1)
    Property.objects.filter(pk=home.pk).update(
        status="verified", is_verified=False, created_at=later
    )
    type(another_user).objects.filter(pk=another_user.pk).update(date_joined=later)
    visit_at(home, another_user, later)
    report = UserReport.objects.create(
        reported_user=another_user, reason="Recorded later"
    )
    UserReport.objects.filter(pk=report.pk).update(created_at=later)
    KYCSubmission.objects.create(
        profile=another_user.profile, status="pending", superseded_at=now
    )
    pending = KYCSubmission.objects.create(
        profile=another_user.profile, status="pending"
    )
    KYCSubmission.objects.filter(pk=pending.pk).update(created_at=later)
    with patch(
        "core_apps.admin_api.services.analytics_service.timezone.now", return_value=now
    ):
        data = get_executive_dashboard_stats()
        overview = get_dashboard_overview_stats()
    metrics = {row["title"]: row["value"] for row in data["executiveMetrics"]}
    assert metrics["العقارات المعتمدة"] == "1"  # Review state, not public availability.
    assert metrics["طلبات الزيارة اليوم"] == "0"
    assert metrics["توثيق معلق"] == "1"
    assert (
        next(row for row in overview["metrics"] if row["icon"] == "clock")["value"]
        == "1"
    )
    assert sum(row["value"] for row in data["reportTrendData"]) == 0
    assert data["monthlyUserChartData"][-1]["label"] == data["period"]["through"]
    future_ids = {f"user-{another_user.id}", f"prop-{home.id}", f"kyc-{pending.id}"}
    assert not future_ids.intersection(row["id"] for row in data["executiveActivities"])
