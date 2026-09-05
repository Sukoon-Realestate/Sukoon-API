import logging
from djoser.email import PasswordChangedConfirmationEmail

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
                "Failed to send password changed confirmation email to %s: %s",
                to,
                exc,
            )
