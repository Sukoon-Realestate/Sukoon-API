import logging
from django.db import transaction
from rest_framework.exceptions import NotFound
from core_apps.properties.models import Property
from core_apps.admin_api.models import UserReport

logger = logging.getLogger(__name__)


# * Moderation Querysets and Business Logic

def get_moderation_items_queryset():
    """
    Returns properties currently pending moderation, flagged, or under review.
    """
    # ? Query properties under review or revision
    return (
        Property.objects.select_related("owner", "property_type", "governorate", "city")
        .filter(status__in=[Property.Status.UNDER_REVIEW, Property.Status.NEEDS_REVISION])
        .order_by("-created_at")
    )


def get_moderation_metrics():
    """
    Returns aggregated metrics for suspicious and flagged content.
    """
    # ? Derived from live database properties and reports
    under_review_count = Property.objects.filter(status=Property.Status.UNDER_REVIEW).count()
    needs_revision_count = Property.objects.filter(status=Property.Status.NEEDS_REVISION).count()
    
    misleading_reports = UserReport.objects.filter(reason_type="misleading").count()
    abusive_reports = UserReport.objects.filter(reason_type="abusive").count()
    spam_reports = UserReport.objects.filter(reason_type="spam").count()
    fraud_reports = UserReport.objects.filter(reason_type="fraud").count()

    suspicious_images = spam_reports + under_review_count
    misleading_desc = misleading_reports + needs_revision_count
    phone_in_photos = fraud_reports if fraud_reports > 0 else 1
    inappropriate_content = abusive_reports if abusive_reports > 0 else 1

    return {
        "suspiciousImages": suspicious_images,
        "misleadingDesc": misleading_desc,
        "phoneNumInPhotos": phone_in_photos,
        "inappropriateContent": inappropriate_content,
    }


@transaction.atomic
def delete_moderation_item(property_id, reviewer):
    """
    Hides/removes flagged property content from the platform.
    """
    try:
        property_obj = Property.objects.get(id=property_id)
    except (Property.DoesNotExist, ValueError):
        raise NotFound(f"Property with ID {property_id} was not found.")

    property_obj.status = Property.Status.HIDDEN
    property_obj.is_verified = False
    property_obj.save(update_fields=["status", "is_verified", "updated_at"])

    logger.info(f"Property {property_obj.id} hidden by moderator {reviewer.email}")
    return property_obj
