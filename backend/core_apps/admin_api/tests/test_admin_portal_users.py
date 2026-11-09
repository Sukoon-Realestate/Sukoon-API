import uuid
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from core_apps.admin_api.models import KYCSubmission, StaffProfile, UserReport
from core_apps.properties.models import Property, PropertyType

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def user_manager(django_user_model):
    u = django_user_model.objects.create_user(
        email="usermanager@sukoon.com",
        password="ValidPassword123!",
        first_name="User",
        last_name="Manager",
        is_staff=True,
    )
    StaffProfile.objects.create(user=u, role_name="main_admin", is_active=True)
    return u


class TestAdminPortalUsers:
    def test_user_list_filters_and_kyc_status(self, api_client, user_manager, make_property):
        api_client.force_authenticate(user=user_manager)
        url = reverse("admin-users-list")

        # Create tenant with pending KYC
        t1 = User.objects.create_user(
            email="tenant_pending@test.com",
            password="Password123!",
            first_name="Ahmed",
            last_name="Ali",
            is_verified=False,
        )
        KYCSubmission.objects.create(
            profile=t1.profile,
            status=KYCSubmission.Status.PENDING,
        )

        # Create tenant with rejected KYC
        t2 = User.objects.create_user(
            email="tenant_rejected@test.com",
            password="Password123!",
            first_name="Sara",
            last_name="Hassan",
            is_verified=False,
        )
        KYCSubmission.objects.create(
            profile=t2.profile,
            status=KYCSubmission.Status.REJECTED,
        )

        # Create verified landlord
        landlord = User.objects.create_user(
            email="landlord_verified@test.com",
            password="Password123!",
            first_name="Mahmoud",
            last_name="Tarek",
            is_verified=True,
        )
        make_property(
            owner=landlord,
            title="Apartment in Zamalek",
            price=15000,
        )

        # 1. Filter kyc_status=pending (Fix for A6-02)
        res = api_client.get(url, {"kyc_status": "pending"})
        assert res.status_code == status.HTTP_200_OK
        emails = [u["email"] for u in res.data["results"]]
        assert "tenant_pending@test.com" in emails
        assert "tenant_rejected@test.com" not in emails
        assert "landlord_verified@test.com" not in emails

        # 2. Filter kyc_status=rejected
        res = api_client.get(url, {"kyc_status": "rejected"})
        assert res.status_code == status.HTTP_200_OK
        emails = [u["email"] for u in res.data["results"]]
        assert "tenant_rejected@test.com" in emails
        assert "tenant_pending@test.com" not in emails

        # 3. Filter kyc_status=verified
        res = api_client.get(url, {"kyc_status": "verified"})
        assert res.status_code == status.HTTP_200_OK
        emails = [u["email"] for u in res.data["results"]]
        assert "landlord_verified@test.com" in emails

        # 4. Filter kyc_status=all
        res = api_client.get(url, {"kyc_status": "all"})
        assert res.status_code == status.HTTP_200_OK

        # 5. Filter role=landlord
        res = api_client.get(url, {"role": "landlord"})
        assert res.status_code == status.HTTP_200_OK
        emails = [u["email"] for u in res.data["results"]]
        assert "landlord_verified@test.com" in emails
        assert "tenant_pending@test.com" not in emails

        # 6. Search filter
        res = api_client.get(url, {"search": "Zamalek"})  # search by name/email
        res2 = api_client.get(url, {"search": "Mahmoud"})
        assert res2.status_code == status.HTTP_200_OK
        assert any(u["email"] == "landlord_verified@test.com" for u in res2.data["results"])

    def test_user_detail_view(self, api_client, user_manager):
        api_client.force_authenticate(user=user_manager)
        target = User.objects.create_user(
            email="target@test.com",
            password="Password123!",
            first_name="Target",
            last_name="User",
        )
        url = reverse("admin-user-detail", kwargs={"user_id": target.id})
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data["id"] == str(target.id)
        assert res.data["email"] == "target@test.com"
        assert res.data["name"] == "Target User"

        # Invalid UUID
        invalid_url = reverse("admin-user-detail-str", kwargs={"user_id": "not-a-uuid"})
        res_invalid = api_client.get(invalid_url)
        assert res_invalid.status_code == status.HTTP_404_NOT_FOUND

        # Nonexistent UUID
        nonexistent_url = reverse("admin-user-detail", kwargs={"user_id": uuid.uuid4()})
        res_none = api_client.get(nonexistent_url)
        assert res_none.status_code == status.HTTP_404_NOT_FOUND

    def test_user_suspend_and_unsuspend_workflow(self, api_client, user_manager):
        api_client.force_authenticate(user=user_manager)
        target = User.objects.create_user(
            email="suspend_target@test.com",
            password="Password123!",
            first_name="Bad",
            last_name="Actor",
            is_active=True,
        )

        suspend_url = reverse("admin-user-suspend", kwargs={"user_id": target.id})
        unsuspend_url = reverse("admin-user-unsuspend", kwargs={"user_id": target.id})

        # Suspend
        res = api_client.post(suspend_url, {"reason": "Fake advertisements"}, format="json")
        assert res.status_code == status.HTTP_200_OK
        target.refresh_from_db()
        assert not target.is_active
        report = UserReport.objects.filter(reported_user=target, status=UserReport.Status.SUSPENDED).first()
        assert report is not None
        assert report.reason == "Fake advertisements"

        # Cannot suspend already suspended
        res_already = api_client.post(suspend_url, {"reason": "Another reason"}, format="json")
        assert res_already.status_code == status.HTTP_400_BAD_REQUEST

        # Unsuspend
        res_un = api_client.post(unsuspend_url, format="json")
        assert res_un.status_code == status.HTTP_200_OK
        target.refresh_from_db()
        assert target.is_active

        # Cannot unsuspend already active
        res_un_again = api_client.post(unsuspend_url, format="json")
        assert res_un_again.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_suspend_staff_or_superuser(self, api_client, user_manager, superuser):
        api_client.force_authenticate(user=user_manager)
        suspend_url = reverse("admin-user-suspend", kwargs={"user_id": superuser.id})
        res = api_client.post(suspend_url, {"reason": "Attempt on admin"}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
