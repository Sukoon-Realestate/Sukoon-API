"""Current finance role and privacy-minimal denial evidence."""

from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from core_apps.admin_api.models import StaffProfile
from ..models import RentalAuditEvent
from .rental_lifecycle.common import staff_role


def require_financial_actor(user, roles, action, *, lock=False):
    query = User.objects.select_for_update() if lock else User.objects
    current = query.get(pk=user.pk)
    if lock:
        StaffProfile.objects.select_for_update().filter(user=current).first()
    if current.sensitive_actions_frozen:
        raise PermissionDenied(
            "New financial actions are restricted; reconcile original instructions separately."
        )
    if not staff_role(current, roles):
        if not lock:
            RentalAuditEvent.objects.create(
                actor=current,
                subject_kind="financial_authority",
                subject_id=current.id,
                subject_revision=0,
                action=action + ".denied",
                reason="Current active finance role is required.",
            )
        raise PermissionDenied(
            "A current active financial operations role is required."
        )
    return current
