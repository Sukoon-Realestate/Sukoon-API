"""Browser administrative sessions obey the existing account recovery boundary."""

import pytest
from django.contrib.auth.base_user import AbstractBaseUser
from django.test import Client, override_settings
from django.urls import reverse
from core_apps.users.models import User
from core_apps.users.services.sessions import issue_refresh, revoke_all, revoke_current


@pytest.fixture
def operator(db, settings):
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    return User.objects.create_user(
        email="isolated-browser-operator@example.invalid",
        password="local-test-password",
        is_staff=True,
        is_superuser=True,
        is_verified=True,
    )


def test_global_revocation_ends_both_original_browser_sessions(operator):
    browsers = [Client(), Client()]
    for browser in browsers:
        browser.force_login(operator)
        assert browser.get(reverse("admin:index")).status_code == 200
    revoke_all(operator, actor=operator, action="session.revoke_all")
    for browser in browsers:
        response = browser.get(reverse("admin:index"))
        assert response.status_code == 302 and "/login/" in response.url
        assert "_auth_user_id" not in browser.session


def test_independent_restriction_revocation_ends_original_browser_authority(operator):
    browser = Client()
    browser.force_login(operator)
    revoke_all(operator, actor=operator, action="account.administrative_restriction", freeze=True)
    response = browser.get(reverse("admin:index"))
    assert response.status_code == 302 and "/login/" in response.url
    assert "_auth_user_id" not in browser.session


def test_frozen_operator_cannot_start_a_new_admin_session_with_password(operator):
    revoke_all(operator, actor=operator, action="account.administrative_restriction", freeze=True)
    browser = Client()
    response = browser.post(
        reverse("admin:login"),
        {
            "username": operator.email,
            "password": "local-test-password",
            "next": reverse("admin:index"),
        },
    )
    assert response.status_code == 200
    assert "_auth_user_id" not in browser.session
    assert "Administrative access is restricted" in response.content.decode()


def test_current_freeze_is_enforced_even_without_a_new_epoch(operator):
    browser = Client()
    browser.force_login(operator)
    User.objects.filter(pk=operator.pk).update(sensitive_actions_frozen=True)
    response = browser.get(reverse("admin:index"))
    assert response.status_code == 302 and "/login/" in response.url


def test_unfrozen_operator_can_sign_in_again_after_revocation(operator):
    revoke_all(operator, actor=operator, action="session.revoke_all")
    browser = Client()
    response = browser.post(
        reverse("admin:login"),
        {
            "username": operator.email,
            "password": "local-test-password",
            "next": reverse("admin:index"),
        },
    )
    assert response.status_code == 302
    assert browser.get(reverse("admin:index")).status_code == 200


def test_zero_epoch_preserves_existing_unrevoked_browser_hash(operator):
    assert operator.security_epoch == 0
    assert operator.get_session_auth_hash() == AbstractBaseUser._get_session_auth_hash(
        operator
    )


def test_secret_rotation_fallback_preserves_current_epoch_session(operator):
    operator = revoke_all(operator, actor=operator, action="session.revoke_all")
    browser = Client()
    with override_settings(SECRET_KEY="isolated-old-key"):
        browser.force_login(operator)
    with override_settings(
        SECRET_KEY="isolated-new-key", SECRET_KEY_FALLBACKS=["isolated-old-key"]
    ):
        assert browser.get(reverse("admin:index")).status_code == 200


def test_current_mobile_session_logout_does_not_revoke_other_browser_session(operator):
    browser = Client()
    browser.force_login(operator)
    token = issue_refresh(operator)
    revoke_current(operator, token.payload)
    operator.refresh_from_db()
    assert operator.security_epoch == 0
    assert browser.get(reverse("admin:index")).status_code == 200
