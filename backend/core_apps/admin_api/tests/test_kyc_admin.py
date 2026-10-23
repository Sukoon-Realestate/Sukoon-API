import pytest
from unittest.mock import patch
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse
from django.utils.html import escape

from core_apps.admin_api.models import KYCSubmission, StaffProfile
from core_apps.users.services.identity_submission import submit_identity


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def admin_static_assets(settings):
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )


@pytest.fixture
def submission(user):
    result = submit_identity(
        user,
        {
            "national_id": "29001011234567",
            "front_id_image": "image/authenticated/v1/front.jpg",
            "back_id_image": "image/authenticated/v1/back.jpg",
        },
    )
    return KYCSubmission.objects.get(id=result["submission_id"])


def review_url(submission):
    return reverse("admin:admin_api_kycsubmission_review", args=[submission.pk])


def test_admin_review_displays_evidence_and_approves(
    client, superuser, user, submission
):
    client.force_login(superuser)
    listing = client.get(reverse("admin:admin_api_kycsubmission_changelist"))
    assert listing.status_code == 200
    assert review_url(submission) in listing.content.decode()
    response = client.get(review_url(submission))
    assert response.status_code == 200
    for field in ("id_face", "id_back"):
        media_url = reverse(
            "admin:admin_api_kycsubmission_media", args=[submission.pk, field]
        )
        assert f'src="{escape(media_url)}"' in response.content.decode()
        with patch(
            "core_apps.profiles.identity_media.identity_bytes",
            return_value=HttpResponse(b"private-image", content_type="image/jpeg"),
        ) as media:
            image = client.get(media_url)
        assert image.status_code == 200
        assert image.content == b"private-image"
        media.assert_called_once_with(submission.evidence_snapshot[field])
    assert response.context["can_review"] is True
    # GET does not make a decision.
    submission.refresh_from_db()
    assert submission.status == "pending"
    response = client.post(review_url(submission), {"decision": "approve"})
    assert response.status_code == 302
    submission.refresh_from_db()
    user.refresh_from_db()
    assert submission.status == "approved"
    assert submission.reviewer == superuser
    assert submission.reviewed_at is not None
    assert user.is_verified


def test_admin_media_rechecks_role(client, another_user, submission):
    another_user.is_staff = True
    another_user.save(update_fields=["is_staff"])
    staff = StaffProfile.objects.create(user=another_user, role_name="kyc_reviewer")
    client.force_login(another_user)
    assert client.get(review_url(submission)).status_code == 200
    staff.is_active = False
    staff.save(update_fields=["is_active"])
    url = reverse(
        "admin:admin_api_kycsubmission_media", args=[submission.pk, "id_face"]
    )
    with patch("core_apps.profiles.identity_media.identity_bytes") as media:
        assert client.get(url).status_code == 403
        media.assert_not_called()


def test_admin_rejection_requires_reason(client, superuser, user, submission):
    client.force_login(superuser)
    response = client.post(
        review_url(submission), {"decision": "reject", "reason": " "}
    )
    assert response.status_code == 200
    submission.refresh_from_db()
    assert submission.status == "pending"
    response = client.post(
        review_url(submission), {"decision": "reject", "reason": "صورة غير واضحة"}
    )
    assert response.status_code == 302
    submission.refresh_from_db()
    user.refresh_from_db()
    assert submission.status == "rejected"
    assert submission.rejection_reason == "صورة غير واضحة"
    assert not user.is_verified


@pytest.mark.parametrize(
    "role,active,allowed",
    [
        ("kyc_reviewer", True, True),
        ("main_admin", True, True),
        ("support", True, False),
        ("kyc_reviewer", False, False),
        (None, True, False),
    ],
)
def test_admin_review_checks_current_role(
    client, another_user, submission, role, active, allowed
):
    another_user.is_staff = True
    another_user.save(update_fields=["is_staff"])
    if role:
        StaffProfile.objects.create(user=another_user, role_name=role, is_active=active)
    client.force_login(another_user)
    response = client.get(review_url(submission))
    assert response.status_code == (200 if allowed else 403)
    response = client.post(review_url(submission), {"decision": "approve"})
    assert response.status_code == (302 if allowed else 403)
    submission.refresh_from_db()
    assert submission.status == ("approved" if allowed else "pending")


def test_admin_cannot_review_own_submission(client, user, submission):
    user.is_superuser = user.is_staff = True
    user.save(update_fields=["is_superuser", "is_staff"])
    client.force_login(user)
    assert client.get(review_url(submission)).context["can_review"] is False
    client.post(review_url(submission), {"decision": "approve"})
    submission.refresh_from_db()
    assert submission.status == "pending"


def test_admin_cannot_approve_superseded_evidence(client, superuser, user, submission):
    submit_identity(user, {"front_id_image": "image/upload/v2/new-front.jpg"})
    client.force_login(superuser)
    assert client.get(review_url(submission)).context["can_review"] is False
    client.post(review_url(submission), {"decision": "approve"})
    submission.refresh_from_db()
    user.refresh_from_db()
    assert submission.status == "pending"
    assert not user.is_verified


def test_admin_default_change_form_cannot_bypass_review(client, superuser, submission):
    client.force_login(superuser)
    url = reverse("admin:admin_api_kycsubmission_change", args=[submission.pk])
    assert client.get(url).status_code == 200
    assert client.post(url, {"status": "approved", "_save": "Save"}).status_code == 403
    submission.refresh_from_db()
    assert submission.status == "pending"


def test_admin_review_requires_csrf(superuser, submission):
    client = Client(enforce_csrf_checks=True)
    client.force_login(superuser)
    assert (
        client.post(review_url(submission), {"decision": "approve"}).status_code == 403
    )
    submission.refresh_from_db()
    assert submission.status == "pending"
