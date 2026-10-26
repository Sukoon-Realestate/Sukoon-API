"""Reuse the installed tour permissions and current administrative authority."""

from core_apps.admin_api.permissions import require_staff_actor
from core_apps.users.totp_models import StaffSecurityIdentity
from .errors import require


def reviewer(user, *, write=False, lock=False):
    current = require_staff_actor(user, lock=lock)
    permission = "change_tourrevision" if write else "view_tourrevision"
    require(
        current.is_staff and current.has_perm(f"virtual_tours.{permission}"),
        "review_forbidden",
        "Current tour review permission is required.",
        403,
    )
    return current


def independent(revision, user):
    target = revision.tour.target
    owner_id = getattr(target, "owner_id", getattr(target, "manager_id", None))
    identities = dict(
        StaffSecurityIdentity.objects.filter(
            user_id__in=[owner_id, user.pk],
        ).values_list("user_id", "person_reference")
    )
    return owner_id != user.pk and not (
        identities.get(owner_id) and identities.get(owner_id) == identities.get(user.pk)
    )
