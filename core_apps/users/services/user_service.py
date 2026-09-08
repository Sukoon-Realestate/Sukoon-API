import logging
from typing import Any
from django.db import transaction

logger = logging.getLogger(__name__)


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
    email = getattr(user, "email", "")

    # * Collect Cloudinary public IDs for best-effort deletion
    cloudinary_public_ids = []

    # Profile images & KYC documents
    profile = getattr(user, "profile", None)
    if profile:
        for attr in ("avatar", "id_face", "id_back", "confirmation_selfi"):
            field = getattr(profile, attr, None)
            if field and hasattr(field, "public_id") and field.public_id:
                cloudinary_public_ids.append(str(field.public_id))

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
            exc,
        )

    # * Permanently delete user from database (triggers CASCADE on all related models)
    user.delete()
    logger.info("Permanently deleted user %s (%s)", user_id, email)

    # * Clean up Cloudinary assets best-effort without blocking or rolling back
    if cloudinary_public_ids:
        try:
            import cloudinary.uploader

            for pid in cloudinary_public_ids:
                try:
                    cloudinary.uploader.destroy(pid)
                except Exception as c_exc:
                    logger.warning(
                        "Cloudinary destroy failed for public_id %s: %s", pid, c_exc
                    )
        except ImportError:
            pass
        except Exception as exc:
            logger.warning(
                "Cloudinary cleanup encountered an error for user %s: %s", user_id, exc
            )
