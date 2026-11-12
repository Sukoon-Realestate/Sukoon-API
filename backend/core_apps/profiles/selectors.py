"""Current account/profile reads and owned, versioned private media selection."""
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework.exceptions import NotFound

from core_apps.users.models import User
from .identity_media import IDENTITY_FIELDS, version
from .models import Profile


def current_profile(user):
    try:
        return Profile.objects.select_related("user").get(user=user)
    except Profile.DoesNotExist:
        raise Http404("Profile is Not found for this user!")


def owned_identity_asset(user, field, requested_version):
    if field not in IDENTITY_FIELDS:
        raise NotFound()
    current = get_object_or_404(User, pk=user.pk, is_active=True)
    profile = get_object_or_404(Profile, user=current)
    asset = getattr(profile, field)
    if not asset or requested_version != version(asset):
        raise NotFound()
    return asset
