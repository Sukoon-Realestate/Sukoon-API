import pytest
from django.urls import reverse
from rest_framework import status
from core_apps.admin_api.models import KYCSubmission, UserReport, StaffProfile


@pytest.mark.django_db
class TestAdminViews:
    def test_unauthenticated_dashboard_returns_401(self, api_client):
        url = reverse("admin-dashboard-stats")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_staff_dashboard_returns_403(self, auth_client, user):
        user.is_staff = False
        user.save()
        url = reverse("admin-dashboard-stats")
        res = auth_client.get(url)
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_authenticated_admin_dashboard(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-dashboard-stats")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    def test_users_list_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-users-list")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    def test_kyc_list_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        KYCSubmission.objects.create(profile=superuser.profile)
        url = reverse("admin-kyc-list")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    def test_reports_list_view(self, api_client, superuser, user):
        api_client.force_authenticate(user=superuser)
        UserReport.objects.create(reported_user=user, reason="Test report")
        url = reverse("admin-reports-list")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    def test_staff_list_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        StaffProfile.objects.create(user=superuser, role_name="system_owner")
        url = reverse("admin-staff-list")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    def test_moderation_list_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-moderation-list")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    def test_moderation_metrics_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-moderation-metrics")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    def test_reports_metrics_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-reports-metrics")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    def test_reports_overview_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-reports-overview")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    def test_support_list_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-support-list")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    def test_support_metrics_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-support-metrics")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    def test_analytics_stats_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-analytics-stats")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    def test_financial_summary_unauthenticated_returns_401(self, api_client):
        url = reverse("admin-financials-summary")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_financial_summary_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-financials-summary")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert "metrics" in res.data
        assert "revenueBreakdown" in res.data
        assert "sixMonthTrend" in res.data

    def test_financial_transactions_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-financials-transactions")
        res = api_client.get(url, {"status": "paid"})
        assert res.status_code == status.HTTP_200_OK
        assert "results" in res.data

    def test_system_health_unauthenticated_returns_401(self, api_client):
        url = reverse("admin-system-health")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_system_health_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-system-health")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert "metrics" in res.data
        assert "auditLogs" in res.data
        assert "apiPerformanceData" in res.data

    def test_system_logs_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-system-logs")
        res = api_client.get(url, {"type": "kyc"})
        assert res.status_code == status.HTTP_200_OK
        assert "results" in res.data

    def test_push_campaigns_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-system-notifications")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK

    def test_send_push_notification_valid(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-system-notifications-send")
        payload = {
            "title": "إشعار اختبار",
            "body": "نص إشعار تجريبي",
            "audience": "all",
        }
        res = api_client.post(url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["title"] == "إشعار اختبار"

    def test_send_push_notification_invalid_body_returns_400(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-system-notifications-send")
        payload = {
            "title": "",
            "body": "",
        }
        res = api_client.post(url, payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_executive_dashboard_unauthenticated_returns_401(self, api_client):
        url = reverse("admin-executive-dashboard")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_executive_dashboard_view(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-executive-dashboard")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert "executiveMetrics" in res.data
        assert "monthlyUserChartData" in res.data
        assert "reportTrendData" in res.data
        assert "userDistribution" in res.data
        assert "executiveActivities" in res.data

    def test_platform_settings_unauthenticated_returns_401(self, api_client):
        url = reverse("admin-settings")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_platform_settings_get_and_post(self, api_client, superuser):
        api_client.force_authenticate(user=superuser)
        url = reverse("admin-settings")
        
        # GET
        get_res = api_client.get(url)
        assert get_res.status_code == status.HTTP_200_OK
        assert "maxReviewHours" in get_res.data

        # POST
        post_res = api_client.post(url, {"maxReviewHours": False, "tenantDocsRequired": True}, format="json")
        assert post_res.status_code == status.HTTP_200_OK
        assert post_res.data["maxReviewHours"] is False
        assert post_res.data["tenantDocsRequired"] is True


