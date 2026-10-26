"""Current finance role and privacy-minimal denial evidence."""

from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from core_apps.admin_api.models import StaffProfile
from ..models import RentalAuditEvent
from .rental_lifecycle.common import staff_role


def authorization_context(user):
    """Invalidate an unsent instruction even when recovery finished while offline."""
    from core_apps.users.models import TotpFactor, TotpRecoveryRequest

    profile = StaffProfile.objects.filter(user=user).first()
    factor = TotpFactor.objects.filter(user=user).first()
    recovery = TotpRecoveryRequest.objects.filter(user=user).order_by("-pk").first()
    return {
        "actor_id": str(user.id),
        "security_epoch": user.security_epoch,
        "factor_revision": factor.revision if factor else None,
        "recovery_id": str(recovery.id) if recovery else None,
        "staff_revision_at": profile.updated_at.isoformat() if profile else None,
    }


def require_financial_actor(user, roles, action, *, lock=False):
    if not getattr(user, "is_authenticated", False) or user.pk is None:
        raise PermissionDenied("A current authenticated financial actor is required.")
    query = User.objects.select_for_update() if lock else User.objects
    current = query.filter(pk=user.pk).first()
    if current is None:
        raise PermissionDenied("A current authenticated financial actor is required.")
    if lock:
        StaffProfile.objects.select_for_update().filter(user=current).first()
    if current.sensitive_actions_frozen:
        raise PermissionDenied(
            "New financial actions are restricted; reconcile original instructions separately."
        )
    from core_apps.users.services.totp import require_sensitive_access

    require_sensitive_access(current)
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
