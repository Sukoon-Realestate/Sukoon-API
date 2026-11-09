"""One listing-image capacity policy for cover and gallery writes (A2-04).

Capacity = stored images + recoverable upload reservations that are still
``pending``/``unknown``. Every writer calls ``require_capacity`` while holding
the listing's ``Property`` row lock (gallery reservation in
``image_uploads.upload``, cover replacement in ``update_property`` and the
legacy ``upload_property_image`` service), so concurrent cover and gallery
writes serialize on that lock and ``images + pending`` can never exceed the
cap. A reservation granted under the lock is honored when its provider upload
completes, which is why pending reservations count here.
"""

from rest_framework.exceptions import ValidationError

from ..listing_media import LISTING_IMAGE_CAP


def upload_operation(property_obj):
    return f"property.image.upload:{property_obj.id}"


def pending_reservations(property_obj):
    from core_apps.features.models import IdempotencyRecord

    return IdempotencyRecord.objects.filter(
        operation=upload_operation(property_obj),
        recovery_status__in=["pending", "unknown"],
    ).count()


def used_capacity(property_obj):
    return property_obj.images.count() + pending_reservations(property_obj)


def require_capacity(property_obj, adding=1):
    """Caller must hold ``select_for_update`` on this property row."""
    if used_capacity(property_obj) + adding > LISTING_IMAGE_CAP:
        raise ValidationError(
            f"A property cannot have more than {LISTING_IMAGE_CAP} images."
        )
