"""First-party Email OTP / staff TOTP adapter for the approved D26 policy."""

from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.utils.translation import get_language
from rest_framework.exceptions import PermissionDenied, Throttled
from ..models import SensitiveAuthorization
from . import totp
from .otp_service import generate_otp, send_otp_email, OTPDeliveryUnavailable


class AccountAssuranceProvider:
    def begin(self, binding):
        item = SensitiveAuthorization.objects.select_related("user").get(
            id=binding["challenge_id"]
        )
        recent = (
            SensitiveAuthorization.objects.filter(
                user=item.user,
                created_at__gte=timezone.now() - timezone.timedelta(seconds=60),
            )
            .exclude(pk=item.pk)
            .exists()
        )
        if recent:
            raise Throttled(wait=60)
        if totp.is_staff_account(item.user):
            factor = totp.current_factor(item.user)
            item.factor_revision = factor.revision
            instructions = (
                "أدخل الرمز الحالي من تطبيق التحقق."
                if (get_language() or "en").startswith("ar")
                else "Enter the current code from your authenticator."
            )
        else:
            if not item.user.is_email_verified:
                raise PermissionDenied(
                    "Verify your email before this sensitive action."
                )
            code = generate_otp()
            item.code_hash = make_password(code)
            if not send_otp_email(item.user.email, code):
                raise OTPDeliveryUnavailable()
            instructions = (
                "أدخل رمز البريد لهذه العملية. ينتهي خلال خمس دقائق."
                if (get_language() or "en").startswith("ar")
                else "Enter the email code for this action. It expires in five minutes."
            )
        item.save(update_fields=["factor_revision", "code_hash", "updated_at"])
        return {
            "reference": str(item.id),
            "public_challenge": {"type": "code", "instructions": instructions},
        }

    def verify(self, reference, assertion, binding):
        item = SensitiveAuthorization.objects.select_related("user").get(id=reference)
        verified = False
        if item.failed_attempts < 5:
            if totp.is_staff_account(item.user):
                factor = totp.current_factor(item.user)
                if factor.revision == item.factor_revision:
                    verified = totp.check_code(factor, assertion)
            elif item.factor_revision is None and item.code_hash:
                verified = (
                    isinstance(assertion, str)
                    and len(assertion) == 6
                    and assertion.isascii()
                    and assertion.isdigit()
                    and check_password(assertion, item.code_hash)
                )
        if not verified:
            item.failed_attempts += 1
            item.save(update_fields=["failed_attempts", "updated_at"])
        return {
            "verified": verified,
            "binding": binding,
            "assurance": "email_otp_or_totp",
        }
