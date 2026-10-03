from datetime import date
import pytest
from django.urls import reverse
from rest_framework import status

from core_apps.admin_api.models import KYCSubmission
from core_apps.profiles.models import Contract, Profile

VERIFICATION_STATUS_URL = reverse("verification-status")
CONTRACTS_URL = reverse("tenant-contracts-list")


@pytest.mark.django_db
class TestVerificationStatusAPI:
    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(VERIFICATION_STATUS_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_incomplete_profile_status(self, auth_client, user):
        user.is_verified = False
        user.save()
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.id_face = None
        profile.id_back = None
        profile.save()

        res = auth_client.get(VERIFICATION_STATUS_URL)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["status"] == "incomplete"
        assert data["rejection_reason"] == ""

    def test_pending_status_from_kyc_submission(self, auth_client, user):
        user.is_verified = False
        user.save()
        profile, _ = Profile.objects.get_or_create(user=user)
        KYCSubmission.objects.create(
            profile=profile,
            status=KYCSubmission.Status.PENDING,
        )

        res = auth_client.get(VERIFICATION_STATUS_URL)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["status"] == "pending"

    def test_approved_status_when_user_is_verified(self, auth_client, user):
        user.is_verified = True
        user.first_name = "كريم"
        user.last_name = "محمود"
        user.save()

        res = auth_client.get(VERIFICATION_STATUS_URL)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["status"] == "approved"
        assert "كريم" in data["full_name"]

    def test_rejected_status_returns_rejection_reason(self, auth_client, user):
        user.is_verified = False
        user.save()
        profile, _ = Profile.objects.get_or_create(user=user)
        KYCSubmission.objects.create(
            profile=profile,
            status=KYCSubmission.Status.REJECTED,
            rejection_reason="صورة بطاقة الهوية غير واضحة",
        )

        res = auth_client.get(VERIFICATION_STATUS_URL)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["status"] == "rejected"
        assert data["rejection_reason"] == "صورة بطاقة الهوية غير واضحة"


@pytest.mark.django_db
class TestTenantContractsAPI:
    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(CONTRACTS_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_empty_contracts_returns_empty_results(self, auth_client, user):
        res = auth_client.get(CONTRACTS_URL)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["count"] == 0
        assert data["results"] == []

    def test_contracts_list_and_user_isolation(self, auth_client, user, another_user):
        Contract.objects.create(
            tenant=user,
            property_title="شقة في المعادي",
            status=Contract.Status.ACTIVE,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            document_url="https://files.example.com/contract.pdf",
        )
        Contract.objects.create(
            tenant=another_user,
            property_title="فيلا في الشيخ زايد",
            status=Contract.Status.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2027, 1, 31),
        )

        res = auth_client.get(f"{CONTRACTS_URL}?page=1&page_size=20")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["property_title"] == "شقة في المعادي"
        assert data["results"][0]["status"] == "active"
        assert (
            data["results"][0]["document_url"]
            == "https://files.example.com/contract.pdf"
        )
