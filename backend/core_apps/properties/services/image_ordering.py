from django.db import transaction
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from core_apps.common.idempotency import IdempotencyConflict
from core_apps.users.models import User
from core_apps.users.services.sessions import validate_session
from ..models import Property


def order_property_images(actor, property_id, data, auth=None):
    """Lock account then listing; identical retries return the current resource.

    Media/review revisions and moderation invalidation commit with the ordering.
    Authorization precedes payload/version errors to preserve the existing contract.
    """
    with transaction.atomic():
        current = User.objects.select_for_update().get(pk=actor.pk)
        if auth:
            validate_session(current, auth)
        prop = Property.objects.select_for_update().filter(id=property_id).first()
        if prop is None:
            raise NotFound()
        if not current.is_active or prop.owner_id != current.pk or prop.retired_at:
            raise PermissionDenied()
        ordered = data.get("image_ids")
        images = list(prop.images.order_by("position", "created_at", "pkid"))
        by_id = {str(image.id): image for image in images}
        categories = data.get("categories", {})
        if (
            not isinstance(categories, dict)
            or set(categories) - set(by_id)
            or any(
                not isinstance(value, str)
                or value
                not in {"bedroom", "living", "kitchen", "bathroom", "exterior", "other"}
                for value in categories.values()
            )
        ):
            raise ValidationError("Supply a known category for each referenced photo.")
        if (
            not isinstance(ordered, list)
            or not ordered
            or any(not isinstance(x, str) for x in ordered)
            or len(ordered) != len(set(ordered))
            or set(ordered) != set(by_id)
        ):
            raise ValidationError("Supply every current image exactly once.")
        if data.get("main_image_id") != ordered[0]:
            raise ValidationError("The first image must be the cover.")
        expected = data.get("expected_revision")
        unchanged = (
            all(by_id[key].room_category == value for key, value in categories.items())
            and [str(image.id) for image in images] == ordered
            and str(prop.main_image) == str(by_id[ordered[0]].image)
        )
        if (
            type(expected) is not int
            or expected != prop.media_revision
            and not unchanged
        ):
            raise IdempotencyConflict(
                "Property photos changed. Reload before reordering."
            )
        if unchanged:
            return prop
        for index, identity in enumerate(ordered):
            image = by_id[identity]
            category = categories.get(identity, image.room_category)
            if image.position != index or image.room_category != category:
                image.position = index
                image.room_category = category
                image.save(update_fields=["position", "room_category"])
        prop.refresh_from_db(
            fields=[
                "media_revision",
                "review_revision",
                "status",
                "is_verified",
                "moderation_blocked",
            ]
        )
        prop.main_image = by_id[ordered[0]].image
        prop.media_revision += 1
        prop.review_revision += 1
        prop.is_verified = False
        if not prop.moderation_blocked and prop.status != Property.Status.HIDDEN:
            prop.status = Property.Status.UNDER_REVIEW
        prop.save(
            update_fields=[
                "main_image",
                "media_revision",
                "review_revision",
                "is_verified",
                "status",
                "updated_at",
            ]
        )
        return prop
