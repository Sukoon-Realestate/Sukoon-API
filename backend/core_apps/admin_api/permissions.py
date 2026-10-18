from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from core_apps.admin_api.models import StaffProfile


def require_staff_actor(user, roles=None, *, lock=False):
    """Read current authority; never trust a cached request-user relationship."""
    query = get_user_model().objects
    if lock:
        query = query.select_for_update()
    current = query.get(pk=user.pk)
    profiles = StaffProfile.objects
    if lock:
        profiles = profiles.select_for_update()
    profile = profiles.filter(user=current).first()
    if not current.is_active or (lock and current.sensitive_actions_frozen):
        raise PermissionDenied("Current active administrative authority is required.")
    if current.is_superuser:
        return current
    if profile is not None:
        allowed = profile.is_active and (roles is None or profile.role_name in roles)
    else:
        allowed = roles is None and current.is_staff
    if not allowed:
        raise PermissionDenied("This action requires a current authorized staff role.")
    return current


class IsAdminStaff(permissions.BasePermission):
    """
    Allows access only to authenticated users who are staff members
    or have an active StaffProfile.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        try:
            require_staff_actor(request.user)
            return True
        except PermissionDenied:
            return False


class IsSystemOwner(permissions.BasePermission):
    """
    Allows access only to system owners or superusers.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        try:
            require_staff_actor(request.user, {StaffProfile.RoleName.SYSTEM_OWNER})
            return True
        except PermissionDenied:
            return False


class IsIdentityReviewer(IsAdminStaff):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        try:
            require_staff_actor(
                request.user,
                {
                    StaffProfile.RoleName.SYSTEM_OWNER,
                    StaffProfile.RoleName.MAIN_ADMIN,
                    StaffProfile.RoleName.KYC_REVIEWER,
                },
            )
            return True
        except PermissionDenied:
            return False


class IsRoleStaff(IsAdminStaff):
    roles = set()

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        try:
            require_staff_actor(request.user, self.roles)
            return True
        except PermissionDenied:
            return False


class IsUserManager(IsRoleStaff):
    roles = {"system_owner", "main_admin"}


class IsPropertyReviewer(IsRoleStaff):
    roles = {"system_owner", "main_admin", "property_reviewer"}


class IsFinancialStaff(IsRoleStaff):
    roles = {
        "system_owner",
        "financial_approver",
        "psp_reconciliation",
        "payout_operator",
        "refund_operator",
    }
