"""Password/activation links are bound to the current account security epoch."""

from django.contrib.auth.tokens import PasswordResetTokenGenerator


class RecoveryTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):

        return super()._make_hash_value(user, timestamp) + f":{user.security_epoch}"


recovery_token_generator = RecoveryTokenGenerator()
