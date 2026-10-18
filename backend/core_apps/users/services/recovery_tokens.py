"""Password/activation links are bound to both account and independent restore epochs."""

from django.contrib.auth.tokens import PasswordResetTokenGenerator


class RecoveryTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        from core_apps.common.recovery import security_epoch

        return (
            super()._make_hash_value(user, timestamp)
            + f":{user.security_epoch}:{security_epoch()}"
        )


recovery_token_generator = RecoveryTokenGenerator()
