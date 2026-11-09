import uuid
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from core_apps.admin_api.models import KYCSubmission, StaffProfile
from core_apps.properties.models import Property, PropertyType
from core_apps.users.services.identity_submission import submit_identity

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def kyc_reviewer(django_user_model):
    u = django_user_model.objects.create_user(
        email="kyc_reviewer@sukoon.com",
        password="ValidPassword123!",
        first_name="KYC",
        last_name="Reviewer",
        is_staff=True,
    )
    StaffProfile.objects.create(user=u, role_name="kyc_reviewer", is_active=True)
    return u


class TestAdminPortalKYC:
    def test_kyc_queue_list_and_filtering(self, api_client, kyc_reviewer, make_property):
        api_client.force_authenticate(user=kyc_reviewer)
        url = reverse("admin-kyc-list")

        # Create tenant submission
        tenant = User.objects.create_user(
            email="tenant_k1@test.com",
            password="Password123!",
            first_name="Kyc",
            last_name="Tenant",
        )
        sub1 = KYCSubmission.objects.create(
            profile=tenant.profile,
            status=KYCSubmission.Status.PENDING,
        )

        # Create landlord submission
        landlord = User.objects.create_user(
            email="landlord_k1@test.com",
            password="Password123!",
            first_name="Kyc",
            last_name="Landlord",
        )
        make_property(owner=landlord, title="Villa in New Cairo", price=25000)
        sub2 = KYCSubmission.objects.create(
            profile=landlord.profile,
            status=KYCSubmission.Status.APPROVED,
        )

        # 1. All queue
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in res.data["results"]]
        assert str(sub1.id) in ids
        assert str(sub2.id) in ids

        # 2. Filter status=pending
        res = api_client.get(url, {"status": "pending"})
        assert res.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in res.data["results"]]
        assert str(sub1.id) in ids
        assert str(sub2.id) not in ids

        # 3. Filter status=all
        res = api_client.get(url, {"status": "all"})
        assert res.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in res.data["results"]]
        assert str(sub1.id) in ids
        assert str(sub2.id) in ids

        # 4. Filter user_type=landlord
        res = api_client.get(url, {"user_type": "landlord"})
        assert res.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in res.data["results"]]
        assert str(sub2.id) in ids
        assert str(sub1.id) not in ids

    def test_kyc_metrics(self, api_client, kyc_reviewer):
        api_client.force_authenticate(user=kyc_reviewer)
        url = reverse("admin-kyc-metrics")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert "pendingReview" in res.data
        assert "acceptedToday" in res.data
        assert "rejectedToday" in res.data
        assert "reviewedToday" in res.data

    def test_kyc_detail_view(self, api_client, kyc_reviewer):
        api_client.force_authenticate(user=kyc_reviewer)
        user = User.objects.create_user(
            email="kyc_detail_user@test.com",
            password="Password123!",
            first_name="Detail",
            last_name="User",
        )
        sub = KYCSubmission.objects.create(
            profile=user.profile,
            status=KYCSubmission.Status.PENDING,
            evidence_snapshot={"national_id": "29501011234567"},
        )

        url = reverse("admin-kyc-detail", kwargs={"submission_id": sub.id})
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data["id"] == str(sub.id)
        assert res.data["userEmail"] == "kyc_detail_user@test.com"
        assert res.data["nationalId"] == "29501011234567"
        assert res.data["status"] == "pending"

        # Not found
        nonexistent = reverse("admin-kyc-detail", kwargs={"submission_id": uuid.uuid4()})
        res_none = api_client.get(nonexistent)
        assert res_none.status_code == status.HTTP_404_NOT_FOUND

    def test_kyc_approve_flow(self, api_client, kyc_reviewer):
        api_client.force_authenticate(user=kyc_reviewer)
        user = User.objects.create_user(
            email="kyc_approve_me@test.com",
            password="Password123!",
            is_verified=False,
        )
        sub_res = submit_identity(
            user,
            {
                "national_id": "29501011234567",
                "front_id_image": "image/authenticated/v1/front.jpg",
                "back_id_image": "image/authenticated/v1/back.jpg",
            },
        )
        sub = KYCSubmission.objects.get(id=sub_res["submission_id"])

        approve_url = reverse("admin-kyc-approve", kwargs={"submission_id": sub.id})
        res = api_client.post(approve_url)
        assert res.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        sub.refresh_from_db()
        assert user.is_verified
        assert sub.status == KYCSubmission.Status.APPROVED
        assert sub.reviewer == kyc_reviewer

    def test_kyc_reject_flow(self, api_client, kyc_reviewer):
        api_client.force_authenticate(user=kyc_reviewer)
        user = User.objects.create_user(
            email="kyc_reject_me@test.com",
            password="Password123!",
            is_verified=False,
        )
        sub_res = submit_identity(
            user,
            {
                "national_id": "29501011234567",
                "front_id_image": "image/authenticated/v1/front.jpg",
                "back_id_image": "image/authenticated/v1/back.jpg",
            },
        )
        sub = KYCSubmission.objects.get(id=sub_res["submission_id"])

        reject_url = reverse("admin-kyc-reject", kwargs={"submission_id": sub.id})

        # Missing reason returns 400
        res_no_reason = api_client.post(reject_url, {"reason": " "}, format="json")
        assert res_no_reason.status_code == status.HTTP_400_BAD_REQUEST

        # Valid reject with document decisions
        payload = {
            "reason": "National ID photo is blurry",
            "document_decisions": {
                "national_id": {"status": "approved", "reason": ""},
                "front_id_image": {"status": "rejected", "reason": "National ID photo is blurry"},
                "back_id_image": {"status": "approved", "reason": ""},
            },
        }
        res = api_client.post(reject_url, payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        sub.refresh_from_db()
        assert not user.is_verified
        assert sub.status == KYCSubmission.Status.REJECTED
        assert sub.rejection_reason == "National ID photo is blurry"

    def test_kyc_media_endpoint_invalid_field(self, api_client, kyc_reviewer):
        api_client.force_authenticate(user=kyc_reviewer)
        user = User.objects.create_user(email="media_test@test.com", password="Password123!")
        sub = KYCSubmission.objects.create(profile=user.profile)
        url = reverse("admin-kyc-media", kwargs={"submission_id": sub.id, "field": "unsupported_field"})
        res = api_client.get(url)
        assert res.status_code == status.HTTP_404_NOT_FOUND
