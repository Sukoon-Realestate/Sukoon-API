"""Mailbox possession is authority for this email change only, never KYC/MFA."""

from datetime import timedelta
import secrets
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction, IntegrityError
from django.utils import timezone, translation
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from ..models import User, EmailChange, AuthSession, SecurityEvent
from .sessions import validate_session
from .otp_service import send_otp_email, OTPDeliveryUnavailable


def message(en, ar):
    return ar if (translation.get_language() or "").startswith("ar") else en


def projection(item):
    from .totp import is_staff_account

    address = item.new_email if item.stage == "verify_new" else item.old_email
    local, domain = address.rsplit("@", 1)
    return {
        "id": str(item.id),
        "stage": item.stage,
        "masked_email": local[:1] + "***@" + domain,
        "expires_at": item.expires_at,
        "resend_at": item.resend_at,
        "staff_verification_required": item.stage == "verify_new"
        and is_staff_account(item.user),
        "verification_email": item.new_email if item.stage == "verify_new" else "",
        **({"email": item.new_email} if item.stage == "complete" else {}),
    }


def _issue(item):
    code = f"{secrets.randbelow(1000000):06d}"
    item.code_hash = make_password(code)
    item.expires_at = timezone.now() + timedelta(minutes=10)
    item.resend_at = timezone.now() + timedelta(seconds=60)
    item.save()
    return code


def _send(item, code):
    email = item.new_email if item.stage == "verify_new" else item.old_email
    if not send_otp_email(email, code):
        # Keep the challenge: SMTP failures can have an unknown outcome.
        raise OTPDeliveryUnavailable()


def start(request):
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=request.user.pk)
        if request.auth:
            validate_session(user, request.auth)
        if not request.auth or not request.auth.get("session_id"):
            raise PermissionDenied(
                message(
                    "Sign in again before changing email.",
                    "سجل الدخول مجددًا قبل تغيير البريد.",
                )
            )
        from .totp import pending_recovery

        if user.sensitive_actions_frozen or pending_recovery(user):
            raise PermissionDenied(
                message("Account recovery is required.", "يلزم استعادة الحساب أولًا.")
            )
        last = EmailChange.objects.filter(user=user).order_by("-created_at").first()
        if last and last.resend_at > timezone.now():
            raise Throttled(
                wait=max(1, int((last.resend_at - timezone.now()).total_seconds()))
            )
        EmailChange.objects.filter(user=user).exclude(
            stage__in=["complete", "cancelled"]
        ).update(stage="cancelled", code_hash="")
        item = EmailChange.objects.create(
            user=user,
            session_id=(request.auth or {}).get("session_id"),
            security_epoch=user.security_epoch,
            old_email=user.email,
            expires_at=timezone.now(),
            resend_at=timezone.now(),
        )
        code = _issue(item)
    _send(item, code)
    return projection(item)


def command(request, identity, action):
    from .totp import pending_recovery

    delivery = None
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=request.user.pk)
        if request.auth:
            validate_session(user, request.auth)
        item = (
            EmailChange.objects.select_for_update()
            .filter(pk=identity, user=user)
            .first()
        )
        if item is None:
            raise NotFound()
        sid = (request.auth or {}).get("session_id")
        if (
            str(item.session_id or "") != str(sid or "")
            or item.security_epoch != user.security_epoch
            or item.old_email.casefold() != user.email.casefold()
            and item.stage != "complete"
            or user.sensitive_actions_frozen
            or pending_recovery(user)
        ):
            raise PermissionDenied(
                message("Verification is no longer valid.", "التحقق لم يعد صالحًا.")
            )
        if action == "status":
            return projection(item), 200
        if action == "cancel":
            if item.stage != "complete":
                item.stage, item.code_hash = "cancelled", ""
                item.save()
            return projection(item), 200
        if item.stage == "complete" and action == "confirm":
            return {**projection(item), "email": user.email}, 200
        if (
            item.stage in ["complete", "cancelled"]
            or item.expires_at <= timezone.now()
            or item.created_at < timezone.now() - timedelta(minutes=30)
        ):
            raise ValidationError(
                message(
                    "Verification expired. Start again.",
                    "انتهت صلاحية التحقق. ابدأ من جديد.",
                )
            )
        if item.attempts >= 5:
            raise ValidationError(
                message(
                    "Too many attempts. Start again.",
                    "تم تجاوز عدد المحاولات. ابدأ من جديد.",
                )
            )
        if action in ["verify-old", "confirm"]:
            expected = "verify_old" if action == "verify-old" else "verify_new"
            if item.stage != expected:
                raise ValidationError(
                    message(
                        "Complete the previous step first.", "أكمل الخطوة السابقة أولًا."
                    )
                )
            code = str(request.data.get("otp", ""))
            if (
                len(code) != 6
                or not code.isascii()
                or not code.isdigit()
                or not check_password(code, item.code_hash)
            ):
                item.attempts += 1
                item.save(update_fields=["attempts", "updated_at"])
                # Return an error after committing the failed attempt.
                return {
                    "message": message(
                        "Incorrect verification code.", "رمز التحقق غير صحيح."
                    )
                }, 400
            if action == "verify-old":
                item.stage, item.code_hash, item.attempts = "enter_new", "", 0
                item.expires_at = timezone.now() + timedelta(minutes=10)
                item.save()
            else:
                from .totp import is_staff_account
                from .sensitive_actions import consume

                if is_staff_account(user):
                    consume(
                        request,
                        action="account.contact.change",
                        resource_id=item.id,
                        revision=0,
                        payload={"email": item.new_email},
                    )
                if (
                    User.objects.filter(email__iexact=item.new_email)
                    .exclude(pk=user.pk)
                    .exists()
                ):
                    raise ValidationError(
                        message(
                            "This email is unavailable.", "البريد الإلكتروني غير متاح."
                        )
                    )
                try:
                    with transaction.atomic():
                        user.email = item.new_email
                        user.is_email_verified = True
                        user.requires_bound_session = True
                        user.save(
                            update_fields=[
                                "email",
                                "is_email_verified",
                                "requires_bound_session",
                            ]
                        )
                except IntegrityError:
                    raise ValidationError(
                        message(
                            "This email is unavailable.", "البريد الإلكتروني غير متاح."
                        )
                    )
                # Keep the authenticated session stable so a lost final reply can
                # be reconciled; revoke every other session and its device tokens.
                others = AuthSession.objects.filter(user=user, revoked_at__isnull=True)
                if sid:
                    others = others.exclude(id=sid)
                revoked_ids = list(others.values_list("pk", flat=True))
                others.update(revoked_at=timezone.now())
                from core_apps.notifications.models import DeviceToken

                DeviceToken.objects.filter(
                    user=user, auth_session_id__in=revoked_ids
                ).update(is_active=False)
                DeviceToken.objects.filter(user=user, auth_session__isnull=True).update(
                    is_active=False
                )
                SecurityEvent.objects.create(
                    user=user,
                    actor=user,
                    action="account.email.changed",
                    security_epoch=user.security_epoch,
                    decision="approved",
                )
                item.stage, item.code_hash = "complete", ""
                item.save()
                EmailChange.objects.filter(user=user).exclude(pk=item.pk).exclude(
                    stage="complete"
                ).update(stage="cancelled", code_hash="")
                from django.core.cache import cache

                cache.delete(f"otp:{item.old_email.lower()}")
                return {**projection(item), "email": user.email}, 200
        elif action == "new-email":
            if item.stage not in ["enter_new", "verify_new"]:
                raise ValidationError(
                    message(
                        "Verify your current email first.", "تحقق من بريدك الحالي أولًا."
                    )
                )
            if item.stage == "verify_new" and item.resend_at > timezone.now():
                raise Throttled(wait=60)
            email = str(request.data.get("email", "")).strip().lower()
            try:
                validate_email(email)
            except DjangoValidationError:
                raise ValidationError(
                    {
                        "email": message(
                            "Enter a valid email.", "أدخل بريدًا إلكترونيًا صحيحًا."
                        )
                    }
                )
            if (
                email.casefold() == user.email.casefold()
                or User.objects.filter(email__iexact=email).exists()
            ):
                raise ValidationError(
                    {
                        "email": message(
                            "This email is unavailable.", "البريد الإلكتروني غير متاح."
                        )
                    }
                )
            item.new_email, item.stage = email, "verify_new"
            delivery = _issue(item)
        elif action == "resend":
            if item.stage not in ["verify_old", "verify_new"]:
                raise ValidationError(
                    message(
                        "No verification code is pending.", "لا يوجد رمز تحقق منتظر."
                    )
                )
            if item.resend_at > timezone.now():
                raise Throttled(
                    wait=max(1, int((item.resend_at - timezone.now()).total_seconds()))
                )
            delivery = _issue(item)
        else:
            raise NotFound()
    if delivery:
        _send(item, delivery)
    return projection(item), 200
