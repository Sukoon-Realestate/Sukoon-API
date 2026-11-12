import logging
from typing import Any
from django.db import transaction, IntegrityError
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)


# * User registration service
@transaction.atomic
def register_user(validated_data: dict, *, dispatch_otp=True, require_activation=False) -> Any:
    """
    ? Creates a new user instance, populates profile fields,
    ? and generates & dispatches an email OTP verification code.
    """
    from django.contrib.auth import get_user_model
    from core_apps.users.services.otp_service import create_and_send_otp

    User = get_user_model()

    data = validated_data.copy()
    birth_date = data.pop("birth_date", None)
    phone_number = data.pop("phone_number", None)
    password = data.pop("password")
    data.pop("re_password", None)

    data["email"] = data["email"].strip().casefold()
    try:
        with transaction.atomic():
            user = User.objects.create_user(password=password, **data)
    except IntegrityError:
        if User.objects.filter(email__iexact=data["email"]).exists():
            raise ValidationError({"email": "This email is unavailable."})
        raise

    if require_activation:
        user.is_active = False
        user.save(update_fields=["is_active"])

    update_fields = []
    if hasattr(user, "profile"):
        if birth_date:
            user.profile.birth_date = birth_date
            update_fields.append("birth_date")
        if phone_number:
            user.profile.phone_number = phone_number
            update_fields.append("phone_number")
        if update_fields:
            user.profile.save(update_fields=update_fields)

    if dispatch_otp:
        create_and_send_otp(user)

    logger.info(
        "Registered user %s.",
        user.id,
    )
    return user


# * User account deletion service
@transaction.atomic
def delete_user_account(user: Any) -> None:
    """
    ? Completely and permanently deletes a user account and associated data.

    ! Cascading foreign keys automatically remove Profile, UserSettings,
    ! SocialAccount, Properties (and their images/amenities/slots),
    ! Visits, Reviews, Saved Properties, Favorites, and Ratings.
    ! Cloudinary assets are cleaned up best-effort.
    """
    user_id = getattr(user, "id", None)

    # * Collect Cloudinary public IDs for best-effort deletion
    cloudinary_public_ids = []

    # Profile images & KYC documents
    profile = getattr(user, "profile", None)
    if profile:
        for attr in ("avatar", "id_face", "id_back", "confirmation_selfi"):
            field = getattr(profile, attr, None)
            if field and hasattr(field, "public_id") and field.public_id:
                cloudinary_public_ids.append(
                    (str(field.public_id), field.type, field.resource_type)
                    if field.type == "authenticated"
                    else str(field.public_id)
                )

    # Property images if user owns listings
    try:
        from core_apps.properties.models import Property

        properties = Property.objects.filter(owner=user).prefetch_related("images")
        for prop in properties:
            if (
                prop.main_image
                and hasattr(prop.main_image, "public_id")
                and prop.main_image.public_id
            ):
                cloudinary_public_ids.append(str(prop.main_image.public_id))
            for img in prop.images.all():
                if (
                    img.image
                    and hasattr(img.image, "public_id")
                    and img.image.public_id
                ):
                    cloudinary_public_ids.append(str(img.image.public_id))
    except Exception as exc:
        logger.warning(
            "Could not inspect properties for Cloudinary cleanup on user %s: %s",
            user_id,
            type(exc).__name__,
        )

    # * Permanently delete user from database (triggers CASCADE on all related models)
    user.delete()
    logger.info("Permanently deleted user %s", user_id)

    # * Clean up Cloudinary assets best-effort without blocking or rolling back
    if cloudinary_public_ids:
        try:
            import cloudinary.uploader

            for pid in cloudinary_public_ids:
                try:
                    if isinstance(pid, tuple):
                        cloudinary.uploader.destroy(
                            pid[0], type=pid[1], resource_type=pid[2], invalidate=True
                        )
                    else:
                        cloudinary.uploader.destroy(pid)
                except Exception as c_exc:
                    logger.warning(
                        "Cloudinary cleanup failed for user %s (%s)",
                        user_id,
                        type(c_exc).__name__,
                    )
        except ImportError:
            pass
        except Exception as exc:
            logger.warning(
                "Cloudinary cleanup encountered an error for user %s (%s)",
                user_id,
                type(exc).__name__,
            )


# * Complete user registration / KYC documents service
@transaction.atomic
def complete_user_registration(
    user: Any, validated_data: dict, *, request_key=None, auth_claims=None
) -> dict:
    """
    Updates missing KYC documents / national ID on user's profile.
    Preserves existing data when fields are omitted.
    Returns registration completion status, verification status, and missing fields list.
    """
    from .identity_submission import submit_identity

    return submit_identity(
        user, validated_data, request_key=request_key, auth_claims=auth_claims
    )


# * Change user password service
@transaction.atomic
def change_user_password(
    user: Any, current_password: str, new_password: str, *, auth_claims=None
) -> None:
    """
    Validates current password, checks usability for social accounts,
    and revokes sessions after a password change.
    Never logs credentials.
    """
    from rest_framework.exceptions import ValidationError
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError as DjangoValidationError

    from core_apps.users.models import User

    snapshot = user
    user = User.objects.select_for_update().get(pk=user.pk)
    from rest_framework_simplejwt.exceptions import AuthenticationFailed
    from .sessions import validate_session

    if not user.is_active or user.closed_at or user.security_epoch != snapshot.security_epoch:
        raise AuthenticationFailed("Session revoked. Sign in again.", code="session_revoked")
    if auth_claims is not None:
        validate_session(user, auth_claims)
    if not user.has_usable_password():
        raise ValidationError(
            {
                "message": "لا يمكن تغيير كلمة المرور لحساب تم تسجيله بواسطة وسائل التواصل الاجتماعي."
            }
        )

    if not user.check_password(current_password):
        raise ValidationError({"current_password": "كلمة المرور الحالية غير صحيحة."})

    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as exc:
        raise ValidationError({"new_password": list(exc.messages)})

    from .passwords import apply_password

    apply_password(user, new_password)
    logger.info("Password changed and sessions revoked")
