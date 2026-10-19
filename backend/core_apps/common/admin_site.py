"""A compromised operator cannot recover authority by opening a new browser."""

from django.contrib.admin import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class RecoveryAdminAuthenticationForm(AdminAuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
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
        return (
            super().has_permission(request)
            and not request.user.sensitive_actions_frozen
        )
