import logging
from djoser.email import (
    PasswordChangedConfirmationEmail,
    PasswordResetEmail,
    ActivationEmail,
)
from djoser.conf import settings as djoser_settings
from .services.recovery_tokens import recovery_token_generator

logger = logging.getLogger(__name__)


class SafePasswordChangedConfirmationEmail(PasswordChangedConfirmationEmail):
    """
    ? Sends a password-changed confirmation email without failing the request
    ? if the mail server is unreachable or times out.
    """

    def send(self, to, *args, **kwargs):
        try:
            super().send(to, *args, **kwargs)
        except Exception as exc:
            # ! Do not fail a successful password change if SMTP fails
            logger.error(
                "Password change notice delivery failed (%s)", type(exc).__name__
            )


class RecoveryPasswordResetEmail(PasswordResetEmail):
    def get_context_data(self):
        context = super().get_context_data()
        context["token"] = recovery_token_generator.make_token(context["user"])
        context["url"] = djoser_settings.PASSWORD_RESET_CONFIRM_URL.format(**context)
        from core_apps.admin_api.models import StaffProfile

        user = context["user"]
        if user.is_superuser or StaffProfile.objects.filter(user=user).exists():
            # Both administrative deployment entries expose this shared route.
            # Ordinary users retain their existing password-recovery destination.
            context["url"] = "admin/password-reset/{uid}/{token}".format(**context)
        return context


class RecoveryActivationEmail(ActivationEmail):
    def get_context_data(self):
        context = super().get_context_data()
        context["token"] = recovery_token_generator.make_token(context["user"])
        context["url"] = djoser_settings.ACTIVATION_URL.format(**context)
        return context
