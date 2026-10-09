from rest_framework.permissions import BasePermission


class HasRentalOperationsRole(BasePermission):
    allowed_roles = set()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        profile = getattr(user, "staff_profile", None)
        required = set(getattr(view, "rental_operations_roles", self.allowed_roles))
        return bool(
            profile
            and profile.is_active
            and profile.role_name in required
        )
