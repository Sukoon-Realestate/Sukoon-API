"""A compromised operator cannot recover authority by opening a new browser."""

from django.contrib.admin import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class RecoveryAdminAuthenticationForm(AdminAuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        from core_apps.admin_api.permissions import require_staff_actor
        from rest_framework.exceptions import PermissionDenied

        try:
            require_staff_actor(user)
        except PermissionDenied as error:
            raise ValidationError(
                _("Current active administrative authority is required."),
                code="inactive_staff",
            ) from error
        if user.sensitive_actions_frozen:
            raise ValidationError(
                _(
                    "Administrative access is restricted while account recovery is pending."
                ),
                code="account_recovery_required",
            )


class SokounAdminSite(AdminSite):
    login_form = RecoveryAdminAuthenticationForm

    def has_permission(self, request):
        if not super().has_permission(request):
            return False
        from core_apps.admin_api.permissions import require_staff_actor
        from rest_framework.exceptions import PermissionDenied

        try:
            current = require_staff_actor(request.user)
            if request.method not in {"GET", "HEAD", "OPTIONS", "TRACE"}:
                from core_apps.users.services.totp import require_sensitive_access

                require_sensitive_access(current)
        except PermissionDenied as error:
            from django.core.exceptions import (
                PermissionDenied as DjangoPermissionDenied,
            )

            raise DjangoPermissionDenied(
                "Current active administrative authority is required."
            ) from error
        return not current.sensitive_actions_frozen
