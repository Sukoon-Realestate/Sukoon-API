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
