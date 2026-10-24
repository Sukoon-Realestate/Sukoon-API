from unittest.mock import patch
from datetime import timedelta
import pytest
from django.utils import timezone
from core_apps.users.models import EmailChange, AuthSession
from core_apps.users.services.sessions import issue_refresh

pytestmark = pytest.mark.django_db


@pytest.fixture
def mailbox(auth_client, user):
    refresh = issue_refresh(user)
    auth_client.force_authenticate(user=user, token=refresh.access_token)
    with patch(
        "core_apps.users.services.email_change.send_otp_email", return_value=True
    ) as mail:
        yield auth_client, mail


def start(client):
    response = client.post("/api/v1/auth/email-change/start/", {}, format="json")
    assert response.status_code == 201, response.data
    return response.data["id"]


def test_email_changes_only_after_both_codes(mailbox, user):
    client, mail = mailbox
    other = issue_refresh(user)
    identity = start(client)
    old = mail.call_args.args[1]
    prefix = f"/api/v1/auth/email-change/{identity}/"
    assert (
        client.post(prefix + "new-email/", {"email": "next@example.com"}).status_code
        == 400
    )
    assert client.post(prefix + "verify-old/", {"otp": old}).status_code == 200
    assert (
        client.post(prefix + "new-email/", {"email": "next@example.com"}).status_code
        == 200
    )
    user.refresh_from_db()
    assert user.email == "user@example.com"
    new = mail.call_args.args[1]
    assert client.post(prefix + "confirm/", {"otp": old}).status_code == 400
    result = client.post(prefix + "confirm/", {"otp": new})
    assert result.status_code == 200, result.data
    user.refresh_from_db()
    assert user.email == "next@example.com"
    assert user.is_email_verified and not user.is_verified
    assert AuthSession.objects.get(id=other["session_id"]).revoked_at
    # A lost final response can be reconciled without sending another code.
    assert client.get(prefix).data["email"] == "next@example.com"
    assert client.post(prefix + "confirm/", {"otp": new}).status_code == 200


def test_failed_attempts_commit_and_are_bounded(mailbox):
    client, mail = mailbox
    identity = start(client)
    for _ in range(6):
        assert (
            client.post(
                f"/api/v1/auth/email-change/{identity}/verify-old/", {"otp": "bad"}
            ).status_code
            == 400
        )
    assert EmailChange.objects.get(pk=identity).attempts == 5
    good = mail.call_args.args[1]
    assert (
        client.post(
            f"/api/v1/auth/email-change/{identity}/verify-old/", {"otp": good}
        ).status_code
        == 400
    )


def test_challenge_cannot_be_used_by_other_session(mailbox, user):
    client, mail = mailbox
    identity = start(client)
    client.force_authenticate(user=user, token=issue_refresh(user).access_token)
    assert (
        client.post(
            f"/api/v1/auth/email-change/{identity}/verify-old/",
            {"otp": mail.call_args.args[1]},
        ).status_code
        == 403
    )


def test_expired_and_cooldown(mailbox):
    client, _ = mailbox
    identity = start(client)
    assert (
        client.post(f"/api/v1/auth/email-change/{identity}/resend/").status_code == 429
    )
    EmailChange.objects.filter(pk=identity).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert (
        client.post(
            f"/api/v1/auth/email-change/{identity}/verify-old/", {"otp": "123456"}
        ).status_code
        == 400
    )


def test_new_mailbox_must_be_unique_case_insensitively(mailbox, another_user):
    client, mail = mailbox
    identity = start(client)
    prefix = f"/api/v1/auth/email-change/{identity}/"
    assert (
        client.post(prefix + "verify-old/", {"otp": mail.call_args.args[1]}).status_code
        == 200
    )
    assert (
        client.post(
            prefix + "new-email/", {"email": another_user.email.upper()}
        ).status_code
        == 400
    )
    assert mail.call_count == 1


def test_email_change_revokes_legacy_tokens_and_unbound_devices(mailbox, user):
    from core_apps.notifications.models import DeviceToken
    from core_apps.users.services.sessions import validate_session
    from rest_framework_simplejwt.exceptions import AuthenticationFailed

    client, mail = mailbox
    device = DeviceToken.objects.create(user=user, token="synthetic-legacy")
    identity = start(client)
    prefix = f"/api/v1/auth/email-change/{identity}/"
    client.post(prefix + "verify-old/", {"otp": mail.call_args.args[1]})
    client.post(prefix + "new-email/", {"email": "changed@example.com"})
    assert (
        client.post(prefix + "confirm/", {"otp": mail.call_args.args[1]}).status_code
        == 200
    )
    user.refresh_from_db()
    device.refresh_from_db()
    assert not device.is_active
    with pytest.raises(AuthenticationFailed):
        validate_session(user, {"security_epoch": 0})


def test_register_rejects_case_variant_of_existing_email(api_client, user):
    with patch("core_apps.users.views_parts.verify_email_apiview.register_user") as register:
        response = api_client.post(
            "/api/v1/auth/register/",
            {
                "email": user.email.upper(),
                "first_name": "Test",
                "last_name": "User",
                "password": "AnotherStrongPass123!",
                "re_password": "AnotherStrongPass123!",
            },
            format="json",
        )
        assert response.status_code == 400, response.data
        assert "email" in response.data["message"].lower()
        register.assert_not_called()


def test_registration_unique_constraint_conflict_is_a_field_error(user):
    from core_apps.users.services.user_service import register_user
    from rest_framework.exceptions import ValidationError

    with pytest.raises(ValidationError) as failure:
        register_user({"email": user.email.upper(), "password": "SyntheticSecret123!"})
    assert "email" in failure.value.detail
