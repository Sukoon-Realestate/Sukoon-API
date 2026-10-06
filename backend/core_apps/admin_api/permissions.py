from rest_framework import permissions


class IsAdminStaff(permissions.BasePermission):
    """
    Allows access only to authenticated users who are staff members
    or have an active StaffProfile.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        return hasattr(request.user, "staff_profile") and request.user.staff_profile.is_active


class IsSystemOwner(permissions.BasePermission):
    """
    Allows access only to system owners or superusers.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        return (
            hasattr(request.user, "staff_profile")
            and request.user.staff_profile.is_active
            and request.user.staff_profile.role_name == "system_owner"
        )
