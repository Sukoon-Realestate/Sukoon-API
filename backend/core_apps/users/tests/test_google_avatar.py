from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from core_apps.profiles.models import Profile, ProfileMediaUpload
from core_apps.profiles.pipeline import save_profile
from core_apps.profiles.services.profile_service import ProfileService
from core_apps.users.services.google_avatar import sync_google_avatar
from core_apps.users.services.social_auth_service_parts.get_or_create_social_user import (
    authenticate_google,
)

pytestmark = pytest.mark.django_db
PHOTO = "https://lh3.googleusercontent.com/a/example-photo=s96-c"
VERIFY = (
    "core_apps.users.services.social_auth_service_parts."
    "get_or_create_social_user._verify_google"
)


def _login(picture=PHOTO):
    with patch(VERIFY, return_value={
        "sub": "google-photo-user", "email": "photo@example.com",
        "email_verified": True, "given_name": "Photo", "family_name": "User",
        "picture": picture,
    }):
        return authenticate_google("verified-token")


def test_google_login_photo_reaches_account_and_profile_reads():
    user = _login()
    profile = Profile.objects.get(user=user)
    assert profile.avatar_url == PHOTO
    assert user.profile.avatar_url == PHOTO
    assert not profile.avatar
    assert ProfileService.get_my_account_data(user)["user"]["avatar"] == PHOTO
    # An external Google image is not an asset uploaded to our Cloudinary account.
    assert not ProfileMediaUpload.objects.filter(user=user).exists()


@pytest.mark.parametrize("route", ["profile-edit", "profile-update"])
def test_profile_screen_and_echo_keep_google_photo_without_an_upload(api_client, route):
    from django.urls import reverse

    user = _login()
    api_client.force_authenticate(user=user)
    response = api_client.patch(reverse(route), {"avatar": PHOTO}, format="json")
    assert response.status_code == 200, response.content
    profile = Profile.objects.get(user=user)
    assert profile.avatar_url == PHOTO and not profile.avatar
    payload = response.json()
    assert payload.get("data", payload)["avatar"] == PHOTO


def test_client_cannot_attach_another_google_photo(auth_client, user):
    from django.urls import reverse

    response = auth_client.patch(
        reverse("profile-edit"), {"avatar": PHOTO}, format="json",
    )
    assert response.status_code == 400
    assert not Profile.objects.get(user=user).google_avatar_url


def test_existing_google_photo_refreshes_on_subsequent_sign_in():
    user = _login()
    replacement = "https://lh3.googleusercontent.com/a/new-photo=s96-c"
    assert _login(replacement).pk == user.pk
    assert Profile.objects.get(user=user).avatar_url == replacement


def test_google_sign_in_keeps_custom_photo():
    user = _login()
    profile = Profile.objects.get(user=user)
    profile.avatar = "profile_documents/avatar/custom-owner-photo"
    profile.save(update_fields=["avatar"])
    _login("https://lh3.googleusercontent.com/a/updated")
    assert Profile.objects.get(user=user).avatar.public_id == (
        "profile_documents/avatar/custom-owner-photo"
    )


@pytest.mark.parametrize("picture", [
    None, "", {}, "http://lh3.googleusercontent.com/a/photo",
    "https://example.com/photo", "https://googleusercontent.com.evil.test/photo",
    "https://user:secret@lh3.googleusercontent.com/a/photo",
    "https://lh3.googleusercontent.com:8443/a/photo",
    "https://lh3.googleusercontent.com/a/photo#fragment",
    "https://lh3.googleusercontent.com/a/" + "x" * 2100,
])
def test_missing_or_invalid_picture_never_breaks_sign_in_or_clears_photo(picture):
    user = _login()
    assert _login(picture).pk == user.pk
    assert Profile.objects.get(user=user).avatar_url == PHOTO


def test_failed_google_verification_cannot_change_an_avatar():
    user = _login()
    with patch(VERIFY, side_effect=ValidationError("Invalid token")):
        with pytest.raises(ValidationError):
            authenticate_google("invalid-token")
    assert Profile.objects.get(user=user).avatar_url == PHOTO


def test_google_oauth_pipeline_uses_the_same_photo_source():
    user = get_user_model().objects.create_user(
        email="pipeline@example.com", first_name="OAuth", last_name="User",
    )
    save_profile(SimpleNamespace(name="google-oauth2"), user, {"picture": PHOTO})
    assert Profile.objects.get(user=user).avatar_url == PHOTO


def test_non_google_pipeline_does_not_import_a_google_photo():
    user = get_user_model().objects.create_user(
        email="other-provider@example.com", first_name="Other", last_name="User",
    )
    save_profile(SimpleNamespace(name="facebook"), user, {"picture": PHOTO})
    assert not Profile.objects.get(user=user).avatar


@pytest.mark.parametrize("closed", [False, True])
def test_unavailable_account_photo_is_not_modified(closed):
    from django.utils import timezone

    user = _login()
    changes = {"closed_at": timezone.now()} if closed else {"is_active": False}
    get_user_model().objects.filter(pk=user.pk).update(**changes)
    sync_google_avatar(user, "https://lh3.googleusercontent.com/a/other")
    assert Profile.objects.get(user=user).avatar_url == PHOTO
