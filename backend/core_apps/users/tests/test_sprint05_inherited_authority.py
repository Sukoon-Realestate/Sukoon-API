"""In-flight inherited actions cannot overwrite closure or revoked authority."""
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from core_apps.users.models import User
from core_apps.users.serializers import CurrentUserSerializer
from core_apps.users.services.sessions import issue_refresh, revoke_all, revoke_current
from core_apps.users.services.user_service import change_user_password

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("path", ["me/", "me.json", "id/", "id.json"])
def test_inflight_inherited_update_cannot_restore_closed_account(user, path):
    token = issue_refresh(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    original = CurrentUserSerializer.validate

    def close_during_validation(serializer, attrs):
        result = original(serializer, attrs)
        User.objects.filter(pk=user.pk).update(
            is_active=False, closed_at=timezone.now(), security_epoch=1, first_name="", last_name="",
        )
        return result

    # Detail uses Djoser's default serializer; patch the base shared validator.
    from djoser.serializers import UserSerializer
    with patch.object(CurrentUserSerializer, "validate", close_during_validation), \
            patch.object(UserSerializer, "validate", close_during_validation):
        response = client.patch("/api/v1/auth/users/" + path.replace("id", str(user.id)),
                                {"first_name": "Must not restore"}, format="json")
    assert response.status_code == 401, response.data
    user.refresh_from_db()
    assert not user.is_active and user.closed_at and user.first_name == ""


@pytest.mark.parametrize("path", ["set_password/", "set_password.json"])
def test_inflight_password_change_rechecks_individual_session_revocation(user, path):
    from core_apps.users.serializers import SetUserPasswordSerializer
    from djoser.serializers import SetPasswordSerializer

    token = issue_refresh(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def revoke_during_validation(serializer, attrs):
        revoke_current(user, token)
        return attrs

    payload = {"current_password": "Testpass123!", "new_password": "NeverApplied123!",
               "re_new_password": "NeverApplied123!"}
    if path.endswith(".json"):
        from core_apps.users.services.passwords import change_inherited_password

        def revoke_before_lock(request, serializer_factory):
            revoke_current(user, token)
            return change_inherited_password(request, serializer_factory)

        with patch("core_apps.users.services.passwords.change_inherited_password", side_effect=revoke_before_lock):
            response = client.post("/api/v1/auth/users/" + path, payload, format="json")
    else:
        with patch.object(SetUserPasswordSerializer, "validate", revoke_during_validation), \
                patch.object(SetPasswordSerializer, "validate", revoke_during_validation):
            response = client.post("/api/v1/auth/users/" + path, payload, format="json")
    assert response.status_code == 401, response.data
    user.refresh_from_db()
    assert user.check_password("Testpass123!")


def test_native_password_service_rejects_stale_account_snapshot(user):
    revoke_all(user)
    with pytest.raises(AuthenticationFailed):
        change_user_password(user, "Testpass123!", "NeverApplied123!")


def test_epoch_bound_activation_cannot_restore_closed_account(user, api_client):
    from core_apps.users.rest_urls import CanonicalUserViewSet
    from djoser.utils import encode_uid

    user.is_active = False
    user.closed_at = timezone.now()
    user.save(update_fields=["is_active", "closed_at"])
    token = CanonicalUserViewSet.token_generator.make_token(user)
    response = api_client.post("/api/v1/auth/users/activation/", {
        "uid": encode_uid(user.pk), "token": token,
    }, format="json")
    assert response.status_code == 403
    user.refresh_from_db()
    assert not user.is_active and user.closed_at


@pytest.mark.parametrize("suffix", ["/", ".json"])
def test_inherited_staff_update_rechecks_current_object_permission(user, another_user, suffix):
    from djoser.serializers import UserSerializer

    user.is_staff = True
    user.save(update_fields=["is_staff"])
    token = issue_refresh(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    original = UserSerializer.validate

    def lose_role(serializer, attrs):
        result = original(serializer, attrs)
        User.objects.filter(pk=user.pk).update(is_staff=False)
        return result

    with patch.object(UserSerializer, "validate", lose_role):
        response = client.patch(f"/api/v1/auth/users/{another_user.id}{suffix}",
                                {"first_name": "Must not edit"}, format="json")
    assert response.status_code in {403, 404}, response.data
    another_user.refresh_from_db()
    assert another_user.first_name == "Another"


def test_inflight_activation_cannot_overwrite_account_closure(user, api_client):
    from djoser.serializers import ActivationSerializer
    from djoser.utils import encode_uid
    from core_apps.users.rest_urls import CanonicalUserViewSet

    user.is_active = False
    user.save(update_fields=["is_active"])
    token = CanonicalUserViewSet.token_generator.make_token(user)
    original = ActivationSerializer.validate

    def close_after_token_validation(serializer, attrs):
        result = original(serializer, attrs)
        User.objects.filter(pk=user.pk).update(
            closed_at=timezone.now(), security_epoch=1, first_name="", last_name="", is_active=False,
        )
        return result

    with patch.object(ActivationSerializer, "validate", close_after_token_validation):
        response = api_client.post("/api/v1/auth/users/activation/", {
            "uid": encode_uid(user.pk), "token": token,
        }, format="json")
    assert response.status_code == 403, response.data
    user.refresh_from_db()
    assert user.closed_at and not user.is_active and user.first_name == ""
