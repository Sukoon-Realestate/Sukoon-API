import uuid
from datetime import timedelta
from types import SimpleNamespace
import pytest
from django.db import transaction
from django.utils import timezone
from core_apps.users.services.recovery_tokens import (
    recovery_token_generator as default_token_generator,
)
from djoser.utils import encode_uid
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from core_apps.users.models import User, SensitiveAuthorization, AuthSession
from core_apps.users.services.sessions import (
    issue_refresh,
    revoke_all,
    revoke_current,
    validate_session,
)
from core_apps.users.services.sensitive_actions import begin, verify, consume
from core_apps.users.token_serializers import CanonicalTokenRefreshSerializer
from core_apps.features.models import PolicyDecision
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.tests.test_cycle_concurrency import parallel_calls

pytestmark = pytest.mark.django_db


class TestAssuranceAdapter:
    test_only = True

    def begin(self, binding):
        return {
            "reference": binding["challenge_id"],
            "public_challenge": {"test_only": True},
        }

    def verify(self, reference, assertion, binding):
        return {
            "verified": assertion == "synthetic-valid-assertion",
            "binding": binding,
            "assurance": "test-strong",
        }


def request_for(user):
    refresh = issue_refresh(user)
    return SimpleNamespace(user=user, auth=refresh.access_token, headers={}, data={})


@pytest.fixture
def assurance(user, settings):
    settings.DEBUG = True
    settings.SECURITY_TEST_BYPASS = False
    settings.SECURITY_ASSURANCE_PROVIDER = __name__ + ".TestAssuranceAdapter"
    policy = PolicyDecision.objects.create(
        evidence_requirements={"fixture": "synthetic only"},
        actions_and_consequences={"fixture": "no live consequence"},
        historical_treatment="No live applicability",
        audit_reason="Isolated test fixture",
        disclosure="Synthetic test only",
        code="D26",
        version="SYNTHETIC-NOT-APPROVED-FOR-PRODUCTION",
        status="approved",
        owner="local-test",
        approver=user,
        source="isolated fixture",
        evidence_reference="unit-test-only",
        scope=["refund.execute", "payout.execute"],
        effective_at=timezone.now() - timedelta(seconds=1),
        rules={
            "provider": settings.SECURITY_ASSURANCE_PROVIDER,
            "proof_lifetime_seconds": 120,
            "assurance": "test-strong",
        },
    )
    return policy


def proof_for(user):
    request = request_for(user)
    data = {
        "action": "refund.execute",
        "resource_id": str(uuid.uuid4()),
        "resource_revision": 3,
        "payload": {"request_key": str(uuid.uuid4()), "amount_minor": 500},
    }
    challenge = begin(request, data)
    proof = verify(request, challenge["id"], "synthetic-valid-assertion")
    request.headers["X-Sokoun-Authorization"] = proof["proof"]
    return request, data


def apply(request, data, **changes):
    params = {
        "action": data["action"],
        "resource_id": data["resource_id"],
        "revision": data["resource_revision"],
        "payload": data["payload"],
        **changes,
    }
    with transaction.atomic():
        consume(request, **params)


def test_reset_revokes_access_refresh_devices_but_keeps_user(user):
    from core_apps.notifications.models import DeviceToken

    request = request_for(user)
    refresh = issue_refresh(user)
    DeviceToken.objects.create(
        user=user, token="synthetic-device", device_type="android"
    )
    revoke_all(user, action="password.reset")
    user.refresh_from_db()
    with pytest.raises(AuthenticationFailed):
        validate_session(user, request.auth)
    with pytest.raises(AuthenticationFailed):
        CanonicalTokenRefreshSerializer().validate({"refresh": str(refresh)})
    assert not DeviceToken.objects.get(user=user).is_active
    assert User.objects.filter(pk=user.pk).exists()
    assert validate_session(user, issue_refresh(user).access_token) == user


def test_reset_endpoint_revokes_existing_session(user):
    refresh = issue_refresh(user)
    client = APIClient()
    response = client.post(
        "/api/v1/auth/users/reset_password_confirm/",
        {
            "uid": encode_uid(user.pk),
            "token": default_token_generator.make_token(user),
            "new_password": "SyntheticChangedPassword123!",
            "re_new_password": "SyntheticChangedPassword123!",
        },
        format="json",
    )
    assert response.status_code == 200, response.data
    user.refresh_from_db()
    with pytest.raises(AuthenticationFailed):
        validate_session(user, refresh.access_token)


def test_logout_revokes_only_current_identified_session(user):
    first, other = issue_refresh(user), issue_refresh(user)
    revoke_current(user, first)
    with pytest.raises(AuthenticationFailed):
        validate_session(user, first)
    assert validate_session(user, other) == user


def test_legacy_token_cannot_survive_recovery(user):
    from rest_framework_simplejwt.tokens import RefreshToken

    old = RefreshToken.for_user(user)
    assert validate_session(user, old) == user
    revoke_all(user)
    user.refresh_from_db()
    with pytest.raises(AuthenticationFailed):
        validate_session(user, old)


@pytest.mark.parametrize(
    "change", ["amount", "resource", "action", "revision", "session"]
)
def test_exact_action_binding(user, assurance, change):
    request, data = proof_for(user)
    with pytest.raises(PermissionDenied):
        if change == "amount":
            apply(request, data, payload={**data["payload"], "amount_minor": 501})
        elif change == "resource":
            apply(request, data, resource_id=uuid.uuid4())
        elif change == "action":
            apply(request, data, action="payout.execute")
        elif change == "revision":
            apply(request, data, revision=4)
        else:
            other = request_for(user)
            other.headers = request.headers
            apply(other, data)
    assert SensitiveAuthorization.objects.get().consumed_at is None
    apply(request, data)
    with pytest.raises(PermissionDenied):
        apply(request, data)


def test_policy_and_provider_missing_never_downgrade(user, settings):
    settings.SECURITY_TEST_BYPASS = False
    request = request_for(user)
    with pytest.raises(RentalConflict) as error:
        begin(
            request,
            {
                "action": "refund.execute",
                "resource_id": uuid.uuid4(),
                "resource_revision": 1,
                "payload": {},
            },
        )
    assert error.value.get_codes() == "awaiting_policy"


def test_security_event_invalidates_proof_and_freeze_preserves_identity(
    user, assurance
):
    request, data = proof_for(user)
    revoke_all(user, freeze=True)
    with pytest.raises(AuthenticationFailed):
        apply(request, data)
    user.refresh_from_db()
    fresh = request_for(user)
    with pytest.raises(PermissionDenied):
        begin(fresh, data)
    assert not SensitiveAuthorization.objects.get().consumed_at


@pytest.mark.django_db(transaction=True)
def test_two_commands_cannot_consume_one_proof(user, assurance):
    request, data = proof_for(user)

    def contender(index):
        try:
            apply(request, data)
            return "consumed"
        except PermissionDenied:
            return "denied"

    assert sorted(parallel_calls(contender)) == ["consumed", "denied"]


def test_proof_rolls_back_with_failed_local_command(user, assurance):
    request, data = proof_for(user)
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            apply(request, data)
            raise RuntimeError("synthetic local rejection before external effect")
    assert SensitiveAuthorization.objects.get().consumed_at is None
    apply(request, data)


@pytest.mark.parametrize("revoked_after_verification", [False, True])
def test_verified_proof_does_not_grant_or_restore_a_financial_role(
    user, assurance, revoked_after_verification
):
    from core_apps.admin_api.models import StaffProfile
    from core_apps.features.models import (
        RentalAuditEvent,
        RentalPayout,
        LedgerTransaction,
    )

    if revoked_after_verification:
        StaffProfile.objects.create(
            user=user, role_name=StaffProfile.RoleName.PAYOUT_OPERATOR
        )
    request = request_for(user)
    payload = {"request_key": str(uuid.uuid4()), "payable_ids": [str(uuid.uuid4())]}
    challenge = begin(
        request,
        {
            "action": "payout.execute",
            "resource_id": uuid.uuid4(),
            "resource_revision": 1,
            "payload": payload,
        },
    )
    proof = verify(request, challenge["id"], "synthetic-valid-assertion")
    if revoked_after_verification:
        StaffProfile.objects.filter(user=user).update(is_active=False)
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {request.auth}",
        HTTP_X_SOKOUN_AUTHORIZATION=proof["proof"],
    )
    response = client.post(
        "/api/v1/features/v1/operations/payouts/execute/", payload, format="json"
    )
    assert response.status_code == 403
    assert "financial operations role" in str(response.data)
    assert SensitiveAuthorization.objects.get(id=challenge["id"]).consumed_at is None
    assert not RentalPayout.objects.exists() and not LedgerTransaction.objects.exists()
    assert RentalAuditEvent.objects.filter(
        actor=user, action="payout.execute.denied"
    ).exists()


def test_logout_deactivates_current_device_but_not_another_session(user):
    from core_apps.notifications.services import NotificationService

    first, second = issue_refresh(user), issue_refresh(user)
    own = NotificationService.register_device_token(
        user, "synthetic-current-device", auth_session=first["session_id"]
    )
    other = NotificationService.register_device_token(
        user, "synthetic-other-device", auth_session=second["session_id"]
    )
    revoke_current(user, first)
    own.refresh_from_db()
    other.refresh_from_db()
    assert not own.is_active and other.is_active
    from rest_framework.exceptions import ValidationError

    with pytest.raises(ValidationError):
        NotificationService.register_device_token(
            user, "synthetic-stale-registration", auth_session=first["session_id"]
        )


def test_removed_compromise_command_has_no_side_effect(user):
    from core_apps.support.models import Ticket
    from core_apps.users.models import SecurityEvent

    request = request_for(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer " + str(request.auth))
    response = client.post(
        "/api/v1/auth/security/sessions/",
        {"action": "report_compromise"}, format="json",
    )
    assert response.status_code == 400
    user.refresh_from_db()
    assert not user.sensitive_actions_frozen and user.security_epoch == 0
    assert not Ticket.objects.exists()
    assert not SecurityEvent.objects.exists()
    assert client.get("/api/v1/auth/security/sessions/").status_code == 200


def test_profile_cannot_change_contact_in_ordinary_patch(user):
    from core_apps.profiles.services import ProfileService

    name = user.first_name
    with pytest.raises(PermissionDenied):
        ProfileService.update_user_profile(
            user, {"full_name": "Unverified change", "phone_number": "+201012345678"}
        )
    user.refresh_from_db()
    assert user.first_name == name and not str(user.profile.phone_number)
    with pytest.raises(PermissionDenied):
        ProfileService.update_user_profile(
            user, {"user": {"email": "different@example.invalid"}}
        )


def test_unverified_invitation_and_activation_cannot_grant_privileged_roles(settings):
    from core_apps.features.services.company.grant_security import (
        require_nonprivileged_onboarding,
    )

    settings.SECURITY_TEST_BYPASS = False
    require_nonprivileged_onboarding(["employee", "coordinator"])
    for role in ["admin", "approver"]:
        with pytest.raises(RentalConflict):
            require_nonprivileged_onboarding([role])
