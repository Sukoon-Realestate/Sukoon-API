from datetime import timedelta
import pytest
from django.utils import timezone
from core_apps.users.models import User
from core_apps.admin_api.services.dashboard_service import (
    get_executive_dashboard_stats,
    get_dashboard_overview_stats,
)

pytestmark = pytest.mark.django_db


def test_empty_dashboard_does_not_invent_activity_or_trends():
    from core_apps.admin_api.services.analytics_service import get_analytics_stats

    data = get_executive_dashboard_stats()
    assert all(metric["value"] == "0" for metric in data["executiveMetrics"])
    assert all(metric["isPositive"] is None for metric in data["executiveMetrics"])
    assert all(
        row["value"] == 0
        for row in data["monthlyUserChartData"] + data["reportTrendData"]
    )
    assert data["executiveActivities"] == []
    assert data["userDistribution"]["total"] == 0
    assert all(
        row["value"] == 0 for row in get_dashboard_overview_stats()["chart_data"]
    )
    analytics = get_analytics_stats()
    assert analytics["visitRequests"] == analytics["completedVisits"] == "0"
    assert analytics["topRegions"] == []
    assert analytics["retentionRate"] == "غير متاح"
    assert all(row["value"] == 0 for row in analytics["dailyChart"])


def test_registration_trend_uses_actual_dates_and_empty_intervals(user):
    old = User.objects.create_user(email="old@example.invalid", password="test")
    User.objects.filter(pk=old.pk).update(
        date_joined=timezone.now() - timedelta(days=60)
    )
    data = get_executive_dashboard_stats()
    assert sum(row["value"] for row in data["monthlyUserChartData"]) == 1
    assert data["monthlyUserChartData"][-1]["value"] == 1
    assert data["userDistribution"]["total"] == 2
    assert all(not row["id"].startswith("eact-") for row in data["executiveActivities"])
