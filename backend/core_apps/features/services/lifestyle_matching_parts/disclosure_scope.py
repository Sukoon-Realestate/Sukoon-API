"""Lifestyle matching: disclosure scope."""

from rest_framework.exceptions import ValidationError
from .profile_extensions import UNKNOWN


def disclosure_scope(user, data, dimensions):
    from ...planning_models import LifestyleProfile

    fields = data.get("share_fields", [])
    if not isinstance(fields, list) or any(
        not isinstance(x, str) or x not in dimensions for x in fields
    ):
        raise ValidationError({"share_fields": "Select lifestyle topic identifiers."})
    profile = LifestyleProfile.objects.filter(user=user).first()
    if fields and (
        profile is None or any(profile.habits.get(x) in UNKNOWN for x in fields)
    ):
        raise ValidationError({"share_fields": "Only answered topics can be shared."})
    if fields:
        from ..planning import check_revision

        check_revision(profile.revision, data.get("share_profile_revision"))
    return {
        "revision": profile.revision if profile else 0,
        "fields": sorted(set(fields)),
    }
