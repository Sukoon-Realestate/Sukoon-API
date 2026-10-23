from unittest.mock import patch
import pytest
from django.core.cache import cache
from rest_framework.exceptions import ValidationError, PermissionDenied
from core_apps.users.services.identity_submission import submit_identity
from core_apps.users.services.otp_service import (
    create_and_send_otp,
    verify_email_otp,
    resend_verification_otp,
    OTPDeliveryUnavailable,
)
from core_apps.admin_api.services.kyc_service import (
    approve_kyc_submission,
    reject_kyc_submission,
    get_kyc_detail,
)
from core_apps.admin_api.models import KYCSubmission
from core_apps.profiles.services import ProfileService

pytestmark = pytest.mark.django_db


def documents(national_id="29001011234567"):
    return {
        "national_id": national_id,
        "front_id_image": "image/upload/v1/front.jpg",
        "back_id_image": "image/upload/v1/back.jpg",
    }


def test_submission_is_queued_immutable_and_retryable(user, superuser):
    result = submit_identity(user, documents(), request_key="initial-identity")
    replay = submit_identity(user, documents(), request_key="initial-identity")
    assert result == replay and result["verification_status"] == "pending"
    assert KYCSubmission.objects.filter(profile=user.profile).count() == 1
    submission = user.profile.kyc_submissions.get()
    assert get_kyc_detail(submission.id)["nationalId"] == documents()["national_id"]
    approve_kyc_submission(submission.id, superuser)
    user.refresh_from_db()
    assert user.is_verified and not user.is_email_verified
    with pytest.raises(ValidationError):
        reject_kyc_submission(submission.id, superuser, "Rewrite approval")
    changed = submit_identity(
        user, documents("29101011234567"), request_key="new-version"
    )
    user.refresh_from_db()
    assert not user.is_verified and changed["submission_id"] != result["submission_id"]
    assert get_kyc_detail(submission.id)["nationalId"] == documents()["national_id"]
    with pytest.raises(ValidationError):
        approve_kyc_submission(submission.id, superuser)


def test_rejected_identity_resubmission_has_new_queue_record(user, superuser):
    first = submit_identity(user, documents())
    reject_kyc_submission(first["submission_id"], superuser, "Supply clearer evidence")
    second = submit_identity(user, documents())
    assert second["submission_id"] != first["submission_id"]
    assert ProfileService.get_verification_status(user)["status"] == "pending"


def test_email_otp_cannot_approve_identity_or_overwrite_rejection(user, superuser):
    result = submit_identity(user, documents())
    reject_kyc_submission(result["submission_id"], superuser, "Mismatch")
    code = create_and_send_otp(user)
    verified = verify_email_otp(user.email, code)
    assert verified.is_email_verified and not verified.is_verified
    assert ProfileService.get_verification_status(verified)["status"] == "rejected"


def test_identity_reviewer_cannot_approve_own_evidence(superuser):
    result = submit_identity(superuser, documents())
    with pytest.raises(PermissionDenied):
        approve_kyc_submission(result["submission_id"], superuser)


def test_email_delivery_failure_is_not_acknowledged_and_retry_is_bounded(user):
    with patch("core_apps.users.services.otp_service.send_mail", return_value=0):
        with pytest.raises(OTPDeliveryUnavailable):
            resend_verification_otp(user.email)
    assert cache.get(f"otp_cooldown:{user.email}")
    with pytest.raises(ValidationError):
        resend_verification_otp(user.email)
    user.refresh_from_db()
    assert not user.is_email_verified and not user.is_verified


def test_identity_migration_preserves_assurance_until_explicit_legacy_review(
    user, superuser
):
    import importlib
    from django.apps import apps
    from django.db import connection
    from django.db.migrations.state import ProjectState
    from core_apps.users.models import User

    legacy = User.objects.create_user(
        email="legacy-review@example.test", password="test", is_verified=True
    )
    legacy.profile.national_id = "29001011234567"
    legacy.profile.id_face = "image/upload/v1/legacy-front.jpg"
    legacy.profile.id_back = "image/upload/v1/legacy-back.jpg"
    legacy.profile.save()
    old = KYCSubmission.objects.create(profile=legacy.profile, status="approved")
    current = submit_identity(user, documents())
    approve_kyc_submission(current["submission_id"], superuser)
    migrate = importlib.import_module(
        "core_apps.admin_api.migrations.0006_reconcile_legacy_identity"
    )
    # Schema rollout must not silently revoke or re-review legacy identities.
    # The explicit review_legacy_identity command owns that separate decision.
    with connection.schema_editor() as editor:
        migrate.Migration("0006_reconcile_legacy_identity", "admin_api").apply(
            ProjectState.from_apps(apps), editor
        )
    legacy.refresh_from_db()
    user.refresh_from_db()
    old.refresh_from_db()
    assert legacy.is_verified and not legacy.is_email_verified
    assert old.status == "approved" and old.superseded_at is None
    assert legacy.profile.kyc_submissions.count() == 1
    assert user.is_verified
