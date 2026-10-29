"""Local R11/R18 contracts. Mail is locmem; no provider/device claim."""

import base64
import uuid
from datetime import timedelta
from types import SimpleNamespace
import pytest
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.admin_api.models import StaffProfile
from core_apps.admin_api.permissions import require_staff_actor
from core_apps.features.models import (
    PolicyDecision,
    LedgerTransaction,
    RentalProviderInstruction,
)
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.users.models import (
    User,
    StaffSecurityIdentity,
    TotpFactor,
    TotpRecoveryRequest,
    TotpEnrollment,
    SensitiveAuthorization,
    SecurityNotice,
    SecurityEvent,
)
from core_apps.users.services.sessions import issue_refresh
from core_apps.users.services import totp, totp_recovery, sensitive_actions
from core_apps.users.services.security_notices import deliver

pytestmark = pytest.mark.django_db


def staff(name, role="payout_operator", person=None, superuser=False):
    user = User.objects.create_user(
        email=f"{name}@example.invalid",
        password="synthetic-local-password",
        is_staff=True,
        is_superuser=superuser,
        is_email_verified=True,
    )
    StaffProfile.objects.create(user=user, role_name=role)
    StaffSecurityIdentity.objects.create(
        user=user,
        person_reference=person or name,
        evidence_reference=f"identity:{name}",
        known_channel_reference=f"known-channel:{name}",
        designated_owner_reviewer=role == "security_recovery_reviewer",
    )
    TotpFactor.objects.create(
        user=user,
        secret_ciphertext=totp.seal(totp.new_secret()),
        confirmed_at=timezone.now(),
    )
    return user


def request(user):
    return SimpleNamespace(
        user=user, auth=issue_refresh(user).access_token, data={}, headers={}
    )


@pytest.fixture
def actors(settings):
    settings.SECURITY_TEST_BYPASS = False
    settings.SECURITY_ASSURANCE_PROVIDER = (
        "core_apps.users.services.assurance.AccountAssuranceProvider"
    )
    employee, reviewer = staff("employee"), staff("reviewer", "system_owner")
    PolicyDecision.objects.create(
        evidence_requirements={"fixture": "local"},
        actions_and_consequences={"fixture": "local"},
        historical_treatment="Local only",
        audit_reason="R11 R18 regression",
        disclosure="Synthetic",
        code="D26",
        version="R11-R18-LOCAL-TEST",
        status="approved",
        owner="test",
        approver=reviewer,
        source="local test",
        evidence_reference="test only",
        scope=sorted(sensitive_actions.ACTIONS),
        effective_at=timezone.now() - timedelta(seconds=1),
        rules={
            "provider": settings.SECURITY_ASSURANCE_PROVIDER,
            "proof_lifetime_seconds": 300,
            "assurance": "email_otp_or_totp",
        },
    )
    return employee, reviewer


def decision_body(item, **changes):
    return {
        "expected_revision": item["revision"],
        "decision": "approve",
        "reason": "Independent identity checked",
        "verification_method": "known_channel_video",
        "verification_reference": "verified-interview:123",
        "identity_matched": True,
        **changes,
    }


def authorize(reviewer_request, item, body):
    # Each test starts with an unused current counter.
    challenge = sensitive_actions.begin(
        reviewer_request,
        {
            "action": "account.totp.recovery.review",
            "resource_id": item["id"],
            "resource_revision": item["revision"],
            "payload": body,
        },
    )
    factor = TotpFactor.objects.get(user=reviewer_request.user)
    code = totp.code_at(
        totp.unseal(factor.secret_ciphertext), int(timezone.now().timestamp()) // 30
    )
    proof = sensitive_actions.verify(reviewer_request, challenge["id"], code)
    reviewer_request.headers["X-Sokoun-Authorization"] = proof["proof"]


def approved(actors):
    employee, reviewer = actors
    applicant, reviewer_request = request(employee), request(reviewer)
    item = totp_recovery.create_request(applicant, "Lost authenticator")
    body = decision_body(item)
    authorize(reviewer_request, item, body)
    item = totp_recovery.decide(reviewer_request, item["id"], body)
    return applicant, reviewer_request, item


def test_rfc_6238_reference_vector():
    secret = base64.b32encode(b"12345678901234567890").decode()
    assert totp.code_at(secret, 59 // 30, digits=8) == "94287082"


def test_non_ascii_authenticator_input_is_an_invalid_attempt(actors):
    employee, _ = actors
    factor = TotpFactor.objects.get(user=employee)
    assert totp.check_code(factor, "١٢٣٤٥٦") is False
    factor.refresh_from_db()
    assert factor.failed_attempts == 1


def test_reviewer_proof_cannot_survive_a_factor_revision_change(actors):
    employee, reviewer = actors
    item = totp_recovery.create_request(request(employee), "Lost device")
    reviewer_request = request(reviewer)
    body = decision_body(item)
    authorize(reviewer_request, item, body)
    factor = TotpFactor.objects.get(user=reviewer)
    factor.revision += 1
    factor.save(update_fields=["revision"])
    with pytest.raises(PermissionDenied):
        totp_recovery.decide(reviewer_request, item["id"], body)
    assert TotpRecoveryRequest.objects.get(id=item["id"]).status == "pending"


def test_limited_recovery_role_is_not_promoted_by_superuser_flag(actors):
    employee, _ = actors
    item = totp_recovery.create_request(request(employee), "Lost device")
    limited = staff("limited-super", "security_recovery_reviewer", superuser=True)
    with pytest.raises(PermissionDenied):
        totp_recovery.decide(request(limited), item["id"], decision_body(item))


def test_request_is_account_scoped_single_and_blocks_existing_proof(actors):
    employee, _ = actors
    first, second = request(employee), request(employee)
    challenge = sensitive_actions.begin(
        first,
        {
            "action": "payout.execute",
            "resource_id": str(uuid.uuid4()),
            "resource_revision": 1,
            "payload": {"amount": 500},
        },
    )
    one = totp_recovery.create_request(first, "Lost device")
    two = totp_recovery.create_request(second, "Second device")
    assert one["id"] == two["id"] and TotpRecoveryRequest.objects.count() == 1
    assert SensitiveAuthorization.objects.get(id=challenge["id"]).consumed_at
    with pytest.raises(PermissionDenied):
        sensitive_actions.verify(first, challenge["id"], "000000")
    assert totp_recovery.status(second)["restricted"]
    assert (
        not LedgerTransaction.objects.exists()
        and not RentalProviderInstruction.objects.exists()
    )


def test_self_review_including_second_superuser_account_is_denied(actors):
    employee, _ = actors
    alternate = staff("alternate", "system_owner", person="employee", superuser=True)
    item = totp_recovery.create_request(request(employee), "Lost device")
    for actor in (employee, alternate):
        with pytest.raises(PermissionDenied):
            totp_recovery.decide(request(actor), item["id"], decision_body(item))


def test_email_session_or_human_note_without_bound_proof_cannot_approve(actors):
    employee, reviewer = actors
    item = totp_recovery.create_request(request(employee), "Lost device")
    with pytest.raises(PermissionDenied):
        totp_recovery.decide(request(reviewer), item["id"], decision_body(item))


def test_revoked_reviewer_role_cannot_use_prior_proof(actors):
    employee, reviewer = actors
    item = totp_recovery.create_request(request(employee), "Lost device")
    reviewer_request = request(reviewer)
    body = decision_body(item)
    authorize(reviewer_request, item, body)
    StaffProfile.objects.filter(user=reviewer).update(role_name="support")
    with pytest.raises(PermissionDenied):
        totp_recovery.decide(reviewer_request, item["id"], body)


def test_approval_invalidates_old_factor_and_is_revision_bound(actors):
    applicant, reviewer, item = approved(actors)
    factor = TotpFactor.objects.get(user=applicant.user)
    assert factor.secret_ciphertext == "" and factor.confirmed_at is None
    assert item["status"] == "approved"
    with pytest.raises(RentalConflict):
        totp_recovery.decide(
            reviewer, item["id"], decision_body(item, expected_revision=1)
        )
    with pytest.raises(PermissionDenied):
        sensitive_actions.begin(
            applicant,
            {
                "action": "payout.execute",
                "resource_id": str(uuid.uuid4()),
                "resource_revision": 1,
                "payload": {},
            },
        )


def test_binding_is_session_bound_and_wrong_codes_persist(actors):
    applicant, _, item = approved(actors)
    enrollment = totp_recovery.enroll(applicant, item["id"])
    assert totp_recovery.enroll(applicant, item["id"])["id"] == enrollment["id"]
    with pytest.raises(PermissionDenied):
        totp_recovery.enroll(request(applicant.user), item["id"])
    for _ in range(5):
        with pytest.raises(ValidationError):
            totp_recovery.confirm(applicant, enrollment["id"], "wrong!")
    factor = TotpFactor.objects.get(user=applicant.user)
    assert factor.failed_attempts == 5 and factor.locked_until > timezone.now()
    code = totp.code_at(enrollment["secret"], int(timezone.now().timestamp()) // 30)
    with pytest.raises(ValidationError):
        totp_recovery.confirm(applicant, enrollment["id"], code)


def test_expired_approval_needs_new_independent_review(actors):
    applicant, _, item = approved(actors)
    TotpRecoveryRequest.objects.filter(id=item["id"]).update(
        approved_at=timezone.now() - timedelta(minutes=6)
    )
    with pytest.raises(PermissionDenied):
        totp_recovery.enroll(applicant, item["id"])


def test_success_and_lost_response_preserve_restrictions_and_money(actors):
    applicant, _, item = approved(actors)
    User.objects.filter(pk=applicant.user.pk).update(sensitive_actions_frozen=True)
    enrollment = totp_recovery.enroll(applicant, item["id"])
    code = totp.code_at(enrollment["secret"], int(timezone.now().timestamp()) // 30)
    result = totp_recovery.confirm(applicant, enrollment["id"], code)
    replay = totp_recovery.confirm(applicant, enrollment["id"], code)
    assert result == replay and result["status"] == "completed"
    assert TotpEnrollment.objects.get(id=enrollment["id"]).secret_ciphertext == ""
    assert totp_recovery.status(applicant)["restricted"]
    assert (
        not LedgerTransaction.objects.exists()
        and not RentalProviderInstruction.objects.exists()
    )
    assert (
        SecurityEvent.objects.filter(action="account.totp.recovery_completed").count()
        == 1
    )


def test_owner_without_designated_reviewer_stays_pending(actors):
    _, owner = actors
    item = totp_recovery.create_request(request(owner), "Lost owner factor")
    late = staff("late-reviewer", "security_recovery_reviewer")
    with pytest.raises(PermissionDenied):
        totp_recovery.decide(request(late), item["id"], decision_body(item))
    assert TotpRecoveryRequest.objects.get(id=item["id"]).status == "pending"


def test_designated_authority_is_limited_and_can_review_sole_owner(actors):
    _, owner = actors
    independent = staff("independent", "security_recovery_reviewer")
    with pytest.raises(PermissionDenied):
        require_staff_actor(independent)
    item = totp_recovery.create_request(request(owner), "Lost owner factor")
    reviewer = request(independent)
    body = decision_body(item)
    authorize(reviewer, item, body)
    assert totp_recovery.decide(reviewer, item["id"], body)["status"] == "approved"


def test_independent_authority_defers_to_available_owner(actors):
    employee, owner = actors
    independent = staff("independent", "security_recovery_reviewer")
    other_owner = staff("other-owner", "system_owner")
    item = totp_recovery.create_request(request(owner), "Lost factor")
    with pytest.raises(PermissionDenied):
        totp_recovery.decide(request(independent), item["id"], decision_body(item))
    assert len(totp_recovery.review_queue(request(other_owner))) == 1


def test_rejection_does_not_reopen_actions(actors):
    employee, reviewer = actors
    applicant = request(employee)
    item = totp_recovery.create_request(applicant, "Lost factor")
    body = decision_body(item, decision="reject")
    actor = request(reviewer)
    authorize(actor, item, body)
    result = totp_recovery.decide(actor, item["id"], body)
    assert (
        result["status"] == "rejected" and totp_recovery.status(applicant)["restricted"]
    )


def test_notice_retry_does_not_repeat_business_event(actors, monkeypatch):
    employee, _ = actors
    item = totp_recovery.create_request(request(employee), "Lost device")
    monkeypatch.setattr(
        "core_apps.users.services.security_notices.send_mail", lambda *a, **k: 0
    )
    assert deliver() == 0
    notice = SecurityNotice.objects.get()
    notification_id = notice.notification_id
    assert notification_id and notice.attempts == 1
    monkeypatch.setattr(
        "core_apps.users.services.security_notices.send_mail", lambda *a, **k: 1
    )
    assert deliver() == 1 and deliver() == 0
    notice.refresh_from_db()
    assert notice.notification_id == notification_id
    assert notice.notification.data["scope"] == "account"
    assert "workspace" not in notice.notification.data
    assert SecurityEvent.objects.filter(subject_id=item["id"]).count() == 1


def test_changed_action_payload_and_wrong_otp_are_rejected(actors):
    employee, reviewer = actors
    item = totp_recovery.create_request(request(employee), "Lost factor")
    body = decision_body(item)
    actor = request(reviewer)
    authorize(actor, item, body)
    with pytest.raises(PermissionDenied):
        totp_recovery.decide(actor, item["id"], {**body, "reason": "Changed details"})


def test_email_otp_does_not_verify_identity_and_attempt_limit_commits(
    actors, mailoutbox
):
    user = User.objects.create_user(
        email="ordinary@example.invalid", password="local", is_email_verified=True
    )
    actor = request(user)
    challenge = sensitive_actions.begin(
        actor,
        {
            "action": "account.contact.change",
            "resource_id": str(user.id),
            "resource_revision": 0,
            "payload": {"email": "new@example.invalid"},
        },
    )
    assert len(mailoutbox) == 1
    for _ in range(6):
        with pytest.raises(PermissionDenied):
            sensitive_actions.verify(actor, challenge["id"], "invalid")
    assert SensitiveAuthorization.objects.get(id=challenge["id"]).failed_attempts == 6
    user.refresh_from_db()
    assert not user.is_verified


@pytest.mark.django_db(transaction=True)
def test_two_devices_create_one_active_request(actors):
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls

    employee, _ = actors
    requests = [request(employee), request(employee)]
    results = parallel_calls(
        lambda index: totp_recovery.create_request(requests[index], "Lost device")["id"]
    )
    assert results[0] == results[1]
    assert TotpRecoveryRequest.objects.filter(user=employee, active=True).count() == 1


@pytest.mark.django_db(transaction=True)
def test_two_independent_decisions_only_approve_once(actors):
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls

    employee, reviewer = actors
    second = staff("second-reviewer", "system_owner")
    item = totp_recovery.create_request(request(employee), "Lost factor")
    body = decision_body(item)
    reviewers = [request(reviewer), request(second)]
    for actor in reviewers:
        authorize(actor, item, body)

    def contender(index):
        try:
            totp_recovery.decide(reviewers[index], item["id"], body)
            return "approved"
        except RentalConflict:
            return "changed"

    assert sorted(parallel_calls(contender)) == ["approved", "changed"]
    recovery = TotpRecoveryRequest.objects.get(id=item["id"])
    assert recovery.decisions.count() == 1
    assert TotpFactor.objects.get(user=employee).revision == 2


def test_mail_failure_never_returns_a_challenge(actors, monkeypatch):
    from core_apps.users.services.otp_service import OTPDeliveryUnavailable

    user = User.objects.create_user(
        email="mail-failure@example.invalid", password="test", is_email_verified=True
    )
    monkeypatch.setattr(
        "core_apps.users.services.assurance.send_otp_email", lambda *args, **kwargs: False
    )
    with pytest.raises(OTPDeliveryUnavailable):
        sensitive_actions.begin(
            request(user),
            {
                "action": "account.contact.change",
                "resource_id": str(user.id),
                "resource_revision": 0,
                "payload": {},
            },
        )
    assert not SensitiveAuthorization.objects.filter(user=user).exists()


def test_information_response_preserves_request_identity_and_history(actors):
    employee, reviewer = actors
    applicant = request(employee)
    item = totp_recovery.create_request(applicant, "Lost factor")
    body = decision_body(item, decision="request_information")
    actor = request(reviewer)
    authorize(actor, item, body)
    decided = totp_recovery.decide(actor, item["id"], body)
    changed = totp_recovery.respond(
        applicant,
        item["id"],
        {
            "expected_revision": decided["revision"],
            "reason": "Additional interview reference",
        },
    )
    assert changed["id"] == item["id"] and changed["status"] == "pending"
    assert len(changed["decisions"]) == 2
    assert totp_recovery.status(applicant)["restricted"]
