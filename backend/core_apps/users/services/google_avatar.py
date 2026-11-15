"""Synchronize a photo supplied by a verified Google identity response."""

from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction

from core_apps.profiles.models import Profile


def _google_photo_url(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if len(value) > Profile._meta.get_field("google_avatar_url").max_length:
        return None
    try:
        URLValidator(schemes=["https"])(value)
        parsed = urlsplit(value)
        host = parsed.hostname or ""
        if parsed.username or parsed.password or parsed.port or parsed.fragment:
            return None
    except (ValidationError, ValueError):
        return None
    if not any(host == domain or host.endswith("." + domain)
               for domain in ("googleusercontent.com", "ggpht.com")):
        return None
    return value


@transaction.atomic
def sync_google_avatar(user, picture):
    """Use Google's verified picture without replacing a custom account photo.

    Call only after provider verification, never with a client-supplied URL.
    Google photos refresh on sign-in; missing/invalid claims are ignored.
    Keep the external URL separate from custom Cloudinary uploads.
    """
    picture = _google_photo_url(picture)
    if picture is None:
        return
    current_user = get_user_model().objects.select_for_update().get(pk=user.pk)
    if not current_user.is_active or current_user.closed_at:
        return
    profile, _ = Profile.objects.get_or_create(user=current_user)
    profile = Profile.objects.select_for_update().get(pk=profile.pk)
    if profile.google_avatar_url != picture:
        profile.google_avatar_url = picture
        profile.save(update_fields=["google_avatar_url", "updated_at"])
    # The caller may still hold the profile cached by the user-creation signal.
    user.profile = profile
