import pytest
from django.urls import reverse
from rest_framework.exceptions import APIException, ValidationError
from core_apps.users.services.identity_submission import submit_identity
from core_apps.admin_api.services.kyc_service import reject_kyc_submission, approve_kyc_submission
from core_apps.admin_api.models import KYCSubmission
from core_apps.profiles.identity_status import current_projection

pytestmark = pytest.mark.django_db


def evidence():
    return {"national_id": "29001011234567", "front_id_image": "image/authenticated/v1/front.jpg", "back_id_image": "image/authenticated/v1/back.jpg"}


def reject_front(user, reviewer):
    original = submit_identity(user, evidence())
    reject_kyc_submission(original["submission_id"], reviewer, "Front blurred", document_decisions={
        "national_id": {"status": "approved"},
        "front_id_image": {"status": "rejected", "reason": "Front blurred"},
        "back_id_image": {"status": "approved"},
    })
    return original


def test_correction_preserves_accepted_evidence_and_previous_snapshot(user, superuser):
    original = reject_front(user, superuser)
    before = current_projection(user)
    result = submit_identity(user, {"expected_revision": before["revision"], "front_id_image": "image/authenticated/v2/front.jpg"}, request_key="correct-front")
    user.profile.refresh_from_db()
    from core_apps.profiles.identity_media import reference
    assert reference(user.profile.id_back).endswith("back.jpg")
    assert user.profile.national_id == evidence()["national_id"]
    old = KYCSubmission.objects.get(id=original["submission_id"])
    assert old.evidence_snapshot["id_face"].endswith("v1/front.jpg")
    latest = KYCSubmission.objects.get(id=result["submission_id"])
    assert latest.document_decisions["back_id_image"]["status"] == "approved"
    assert result["verification_status"] == "pending"
    user.refresh_from_db()
    assert not user.is_verified


def test_changed_reviewer_decision_rejects_stale_edit_before_upload(user, superuser):
    original = submit_identity(user, evidence())
    before = current_projection(user)
    reject_kyc_submission(original["submission_id"], superuser, "Correction needed")
    with pytest.raises(APIException) as error:
        submit_identity(user, {"expected_revision": before["revision"], "front_id_image": "new-front"})
    assert error.value.status_code == 409
    assert KYCSubmission.objects.filter(profile=user.profile).count() == 1


def test_accepted_document_cannot_be_overwritten_even_by_legacy_client(user, superuser):
    reject_front(user, superuser)
    with pytest.raises(ValidationError):
        submit_identity(user, {"back_id_image": "replacement"})


def test_original_operation_replays_after_review_without_creating_submission(user, superuser):
    reject_front(user, superuser)
    body = {"expected_revision": current_projection(user)["revision"], "front_id_image": "image/authenticated/v2/front.jpg"}
    first = submit_identity(user, body, request_key="same-correction")
    approve_kyc_submission(first["submission_id"], superuser)
    assert submit_identity(user, body, request_key="same-correction") == first
    assert KYCSubmission.objects.filter(profile=user.profile).count() == 2


def test_status_projection_is_private_and_scoped(auth_client, user, another_user, superuser):
    reject_front(user, superuser)
    submit_identity(another_user, evidence())
    response = auth_client.get(reverse("verification-status"))
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    data = response.json()["data"]
    assert data["status"] == "rejected"
    fields = {row["field"]: row for row in data["documents"]}
    assert fields["front_id_image"]["can_replace"]
    assert not fields["back_id_image"]["can_replace"]
    raw = str(data)
    assert "authenticated/" not in raw and evidence()["national_id"] not in raw


@pytest.mark.parametrize("decisions", [{"front_id_image": {"status": "approved"}}, {"foreign": {"status": "rejected", "reason": "x"}}, {"front_id_image": {"status": "rejected", "reason": ""}}])
def test_partial_or_invalid_decision_cannot_silently_accept_other_documents(user, superuser, decisions):
    original = submit_identity(user, evidence())
    with pytest.raises(ValidationError):
        reject_kyc_submission(original["submission_id"], superuser, "Check", document_decisions=decisions)
    assert KYCSubmission.objects.get(id=original["submission_id"]).status == "pending"


def test_closed_unknown_upload_cannot_arrive_late(user):
    from core_apps.common.idempotency import resolve_or_close, IdempotencyConflict
    identity = "50e6bbdf-795e-4141-9134-48fa4217b8e8"
    closed = resolve_or_close(user=user, operation="identity.submit", key=identity)
    assert closed.recovery_status == "absent_final"
    with pytest.raises(IdempotencyConflict):
        submit_identity(user, evidence(), request_key=identity)
    assert not KYCSubmission.objects.filter(profile=user.profile).exists()


def test_resolve_is_account_scoped_and_returns_original_receipt(auth_client, user, another_user):
    identity = "50e6bbdf-795e-4141-9134-48fa4217b8e8"
    submit_identity(another_user, evidence(), request_key=identity)
    response = auth_client.post(reverse("identity-operation-resolve", args=[identity]), {}, format="json")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "absent_final" and data["result"] is None


def test_new_mobile_identity_errors_are_localized():
    from core_apps.common.translation import translate_message
    for message in ["Identity review changed. Refresh before submitting.", "This identity document cannot be replaced in the current review."]:
        assert translate_message(message, "ar") != message
        assert translate_message(message, "en") == message
