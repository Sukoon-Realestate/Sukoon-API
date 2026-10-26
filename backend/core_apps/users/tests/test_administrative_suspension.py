"""Reactivation never resurrects pre-suspension access or verification."""

import pytest
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from core_apps.admin_api.services.user_service import suspend_user, unsuspend_user
from core_apps.users.models import AuthSession
from core_apps.users.services.sessions import issue_refresh, validate_session
from core_apps.users.token_serializers import CanonicalTokenRefreshSerializer


@pytest.mark.django_db
def test_reactivation_requires_new_login(user, superuser):
    from core_apps.notifications.models import DeviceToken

    refresh = issue_refresh(user)
    DeviceToken.objects.create(
        user=user, token="suspension-test", device_type="android"
    )
    suspended = suspend_user(user.id, superuser)
    assert not suspended.is_active
    assert suspended.security_epoch == 1
    assert not AuthSession.objects.filter(user=user, revoked_at__isnull=True).exists()
    assert not DeviceToken.objects.get(user=user).is_active
    active = unsuspend_user(user.id, superuser)
    assert active.is_active and active.security_epoch == 1
    with pytest.raises(AuthenticationFailed):
        validate_session(active, refresh.access_token)
    with pytest.raises(AuthenticationFailed):
        CanonicalTokenRefreshSerializer().validate({"refresh": str(refresh)})
    assert validate_session(active, issue_refresh(active).access_token) == active


@pytest.mark.django_db
def test_django_admin_suspension_revokes_and_preserves_existing_epoch(user, superuser):
    from types import SimpleNamespace
    from django.contrib.admin.sites import AdminSite
    from core_apps.users.admin import UserAdmin
    from core_apps.users.models import User
    from core_apps.users.services.sessions import revoke_all

    old = issue_refresh(user)
    stale_form_user = User.objects.get(pk=user.pk)
    revoke_all(user, actor=superuser, action="account.sessions_revoked")
    model_admin = UserAdmin(User, AdminSite())
    stale_form_user.is_active = False
    model_admin.save_model(SimpleNamespace(user=superuser), stale_form_user, None, True)
    user.refresh_from_db()
    assert user.security_epoch == 2
    assert not user.is_active
    user.is_active = True
    model_admin.save_model(SimpleNamespace(user=superuser), user, None, True)
    with pytest.raises(AuthenticationFailed):
        validate_session(user, old.access_token)
