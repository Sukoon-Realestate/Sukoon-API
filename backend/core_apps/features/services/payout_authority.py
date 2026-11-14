"""Fresh payout roles for new commands and original instruction review."""

from core_apps.admin_api.models import StaffProfile
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from core_apps.features.services.rental_lifecycle.common import staff_role


def _require_payout_role(user, *, lock=False):
    from ..services.financial_authority import require_financial_actor

    return require_financial_actor(
        user, {StaffProfile.RoleName.PAYOUT_OPERATOR}, "payout.execute", lock=lock
    )


def _reader(user):
    current = User.objects.get(pk=user.pk)
    if not staff_role(
        current,
        {
            StaffProfile.RoleName.PAYOUT_OPERATOR,
            StaffProfile.RoleName.PSP_RECONCILIATION,
        },
    ):
        raise PermissionDenied("A current payout review role is required.")
    return current


__all__ = ["_reader", "_require_payout_role"]
