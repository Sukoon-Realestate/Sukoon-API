import uuid
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from core_apps.admin_api.models import StaffProfile, StaffAuthorityAudit

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def system_owner(django_user_model):
    u = django_user_model.objects.create_user(
        email="sysowner@sukoon.com",
        password="ValidPassword123!",
        first_name="System",
        last_name="Owner",
        is_staff=True,
        is_superuser=True,
    )
    StaffProfile.objects.create(user=u, role_name="system_owner", is_active=True)
    return u


@pytest.fixture
def support_staff(django_user_model):
    u = django_user_model.objects.create_user(
        email="supportstaff@sukoon.com",
        password="ValidPassword123!",
        first_name="Support",
        last_name="Agent",
        is_staff=True,
    )
    StaffProfile.objects.create(user=u, role_name="support", is_active=True)
    return u


class TestAdminPortalStaffAndRoles:
    def test_staff_list_and_roles_summary(self, api_client, system_owner):
        api_client.force_authenticate(user=system_owner)

        list_url = reverse("admin-staff-list")
        res = api_client.get(list_url)
        assert res.status_code == status.HTTP_200_OK
        emails = [s["email"] for s in res.data["results"]]
        assert "sysowner@sukoon.com" in emails

        roles_url = reverse("admin-roles-summary")
        r_res = api_client.get(roles_url)
        assert r_res.status_code == status.HTTP_200_OK
        assert len(r_res.data) > 0
        role_names = [r["name"] for r in r_res.data]
        assert any("مالك النظام" in name for name in role_names) or any("مشرف رئيسي" in name for name in role_names)

    def test_staff_invite_and_delete_workflow(self, api_client, system_owner):
        api_client.force_authenticate(user=system_owner)

        invite_url = reverse("admin-staff-invite")
        payload = {
            "name": "Nour Ibrahim",
            "email": "nour.ibrahim@sukoon.com",
            "role_name": "kyc_reviewer",
            "reason": "Expanding KYC review team",
        }

        # 1. Invite new staff
        res = api_client.post(invite_url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert "تمت إضافة المشرف" in res.data["message"]

        new_user = User.objects.get(email="nour.ibrahim@sukoon.com")
        profile = StaffProfile.objects.get(user=new_user)
        assert profile.is_active is True
        assert profile.role_name == "kyc_reviewer"

        audit = StaffAuthorityAudit.objects.filter(target=new_user, action="grant").first()
        assert audit is not None
        assert audit.actor == system_owner

        # 2. Delete staff member
        delete_url = reverse("admin-staff-delete", kwargs={"staff_id": profile.id})
        del_res = api_client.delete(delete_url, {"reason": "End of contract"}, format="json")
        assert del_res.status_code == status.HTTP_200_OK
        profile.refresh_from_db()
        assert profile.is_active is False

        del_audit = StaffAuthorityAudit.objects.filter(target=new_user, action="revoke").first()
        assert del_audit is not None

    def test_non_system_owner_cannot_invite_staff(self, api_client, support_staff):
        api_client.force_authenticate(user=support_staff)
        invite_url = reverse("admin-staff-invite")
        payload = {
            "name": "Unauthorized Add",
            "email": "unauth@sukoon.com",
            "role_name": "main_admin",
            "reason": "Test",
        }
        res = api_client.post(invite_url, payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_system_owner_cannot_delete_self(self, api_client, system_owner):
        api_client.force_authenticate(user=system_owner)
        owner_profile = StaffProfile.objects.get(user=system_owner)
        delete_url = reverse("admin-staff-delete", kwargs={"staff_id": owner_profile.id})
        res = api_client.delete(delete_url, {"reason": "Self delete"}, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_permissions_matrix_view(self, api_client, system_owner):
        api_client.force_authenticate(user=system_owner)
        matrix_url = reverse("admin-permissions-matrix")
        res = api_client.get(matrix_url)
        assert res.status_code == status.HTTP_200_OK
        assert isinstance(res.data, list)
        assert len(res.data) > 0
        assert "action" in res.data[0]
        assert "systemOwner" in res.data[0]
