"""A1-03 failing-before case: social sign-in must not adopt an attacker's pre-registered credentials.

get_or_create_social_user links a provider-verified email to an existing local account and
marks it verified without retiring the existing password. An attacker who pre-registered the
victim's email keeps a working password. Strict xfail: the Sprint 01 fix must make this pass.
"""

import pytest
from django.contrib.auth import get_user_model

from core_apps.users.services.social_auth_service_parts.get_or_create_social_user import (
    get_or_create_social_user,
)

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.xfail(strict=True, reason="A1-03: auto-link keeps the pre-registered password usable (Sprint 01)")
def test_verified_social_login_retires_attacker_preregistered_password():
    User.objects.create_user(
        email="victim@example.com", first_name="Pre", last_name="Registered", password="attacker-secret"
    )

    owner = get_or_create_social_user(
        provider="google", provider_uid="google-victim-uid", email="victim@example.com",
        email_verified=True, first_name="Rightful", last_name="Owner",
    )

    owner.refresh_from_db()
    assert not owner.check_password("attacker-secret"), "attacker credentials survive social adoption"
