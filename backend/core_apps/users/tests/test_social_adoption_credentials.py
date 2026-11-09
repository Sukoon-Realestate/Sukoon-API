"""A1-03: social sign-in must not adopt an attacker's pre-registered credentials.

Sprint 00 recorded this as a strict xfail. Sprint 01 retires unproven local credentials
and sessions when a provider-verified identity adopts an unverified account, while keeping
established (email-verified) accounts' passwords.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied, ValidationError

from core_apps.users.models import AuthSession, SecurityEvent, SocialAccount
from core_apps.users.services.social_auth_service_parts.get_or_create_social_user import (
    get_or_create_social_user,
)

User = get_user_model()
pytestmark = pytest.mark.django_db


def _social(email="victim@example.com", uid="google-victim-uid"):
    return get_or_create_social_user(
        provider="google", provider_uid=uid, email=email,
        email_verified=True, first_name="Rightful", last_name="Owner",
    )


def test_verified_social_login_retires_attacker_preregistered_password():
    pre = User.objects.create_user(
        email="victim@example.com", first_name="Pre", last_name="Registered", password="attacker-secret"
    )
    epoch = pre.security_epoch

    owner = _social()

    owner.refresh_from_db()
    assert owner.pk == pre.pk
    assert not owner.check_password("attacker-secret"), "attacker credentials survive social adoption"
    assert owner.is_email_verified
    assert owner.security_epoch == epoch + 1
    assert not AuthSession.objects.filter(user=owner, revoked_at__isnull=True).exists()
    assert SecurityEvent.objects.filter(user=owner, action="account.social_adoption").exists()


def test_established_verified_account_keeps_its_password():
    existing = User.objects.create_user(
        email="owner@example.com", first_name="A", last_name="B", password="owners-own-secret"
    )
    User.objects.filter(pk=existing.pk).update(is_email_verified=True)

    linked = _social(email="owner@example.com", uid="google-owner")

    assert linked.pk == existing.pk
    assert linked.check_password("owners-own-secret")
    assert SocialAccount.objects.filter(user=existing, provider_uid="google-owner").exists()


def test_existing_link_is_reused_and_uid_collision_is_explicit():
    first = _social(email="new@example.com", uid="uid-1")
    again = _social(email="new@example.com", uid="uid-1")
    assert again.pk == first.pk
    assert SocialAccount.objects.filter(provider_uid="uid-1").count() == 1

    other = User.objects.create_user(email="other@example.com", first_name="O", last_name="T", password="x")
    User.objects.filter(pk=other.pk).update(is_email_verified=True)
    # The same provider uid presented with a different email still resolves to its link.
    assert _social(email="other@example.com", uid="uid-1").pk == first.pk


@pytest.mark.parametrize("state", ["inactive", "closed"])
def test_suspended_or_closed_accounts_are_not_adopted(state):
    from django.utils import timezone

    user = User.objects.create_user(email="gone@example.com", first_name="G", last_name="O", password="pw")
    update = {"is_active": False} if state == "inactive" else {"closed_at": timezone.now()}
    User.objects.filter(pk=user.pk).update(**update)
    with pytest.raises(PermissionDenied):
        _social(email="gone@example.com", uid=f"uid-{state}")
    assert not SocialAccount.objects.filter(user=user).exists()


def test_unverified_provider_email_never_links():
    User.objects.create_user(email="target@example.com", first_name="T", last_name="T", password="pw")
    with pytest.raises(ValidationError):
        get_or_create_social_user(
            provider="google", provider_uid="uid-unverified", email="target@example.com",
            email_verified=False, first_name="X", last_name="Y",
        )
