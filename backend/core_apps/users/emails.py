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
        return context


class RecoveryActivationEmail(ActivationEmail):
    def get_context_data(self):
        context = super().get_context_data()
        context["token"] = recovery_token_generator.make_token(context["user"])
        context["url"] = djoser_settings.ACTIVATION_URL.format(**context)
        return context
