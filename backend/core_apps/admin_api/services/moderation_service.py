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
        .filter(
            status__in=[Property.Status.UNDER_REVIEW, Property.Status.NEEDS_REVISION]
        )
        .order_by("-created_at")
    )


def get_moderation_metrics():
    """
    Returns aggregated metrics for suspicious and flagged content.
    """
    # ? Derived from live database properties and reports
    under_review_count = Property.objects.filter(
        status=Property.Status.UNDER_REVIEW
    ).count()
    needs_revision_count = Property.objects.filter(
        status=Property.Status.NEEDS_REVISION
    ).count()

    misleading_reports = UserReport.objects.filter(reason_type="misleading").count()
    abusive_reports = UserReport.objects.filter(reason_type="abusive").count()
    spam_reports = UserReport.objects.filter(reason_type="spam").count()
    fraud_reports = UserReport.objects.filter(reason_type="fraud").count()

    suspicious_images = spam_reports + under_review_count
    misleading_desc = misleading_reports + needs_revision_count
    phone_in_photos = fraud_reports
    inappropriate_content = abusive_reports

    return {
        "suspiciousImages": suspicious_images,
        "misleadingDesc": misleading_desc,
        "phoneNumInPhotos": phone_in_photos,
        "inappropriateContent": inappropriate_content,
    }


@transaction.atomic
def delete_moderation_item(property_id, reviewer):
    """
    Hides/removes flagged property content from the platform enforcing canonical moderation invariants.
    """
    from core_apps.admin_api.permissions import require_staff_actor
    from core_apps.users.services.totp import require_sensitive_access
    from rest_framework.exceptions import PermissionDenied, ValidationError
    from core_apps.properties.models import PropertyModerationDecision
    from core_apps.properties.services.moderation import snapshot
    from core_apps.common.idempotency import fingerprint
    from core_apps.features.models import RentalAuditEvent
    from core_apps.features.planning_models import PlanningEvent

    staff_reviewer = require_staff_actor(
        reviewer, {"system_owner", "main_admin", "property_reviewer"}, lock=True
    )
    require_sensitive_access(staff_reviewer)

    try:
        property_obj = Property.objects.select_for_update().get(id=property_id)
    except (Property.DoesNotExist, ValueError):
        raise NotFound(f"Property with ID {property_id} was not found.")

    if property_obj.owner_id == reviewer.pk:
        raise PermissionDenied(
            "An independent moderation reviewer is required; cannot moderate own property."
        )

    if property_obj.retired_at:
        raise ValidationError("Retired inventory cannot be republished or modified.")

    before_status = property_obj.status
    observed = snapshot(property_obj)
    expected_version = fingerprint(observed)

    decision = PropertyModerationDecision.objects.create(
        property=property_obj,
        reviewer=reviewer,
        source_revision=property_obj.review_revision,
        source_version=expected_version,
        snapshot=observed,
        action="block",
        public_reason="Flagged content removed by admin moderation",
        internal_note="Removed via admin portal moderation action",
    )

    property_obj.is_verified = False
    property_obj.moderation_blocked = True
    property_obj.moderation_reason = "Flagged content removed by admin moderation"
    property_obj.status = Property.Status.HIDDEN
    property_obj.review_revision += 1
    property_obj.save(
        update_fields=[
            "status",
            "is_verified",
            "moderation_blocked",
            "moderation_reason",
            "review_revision",
            "updated_at",
        ]
    )

    RentalAuditEvent.objects.create(
        actor=reviewer,
        subject_kind="property",
        subject_id=property_obj.id,
        subject_revision=decision.source_revision,
        action="property.moderation.block",
        reason="Flagged content removed by admin moderation",
        metadata={
            "decision_id": str(decision.id),
            "version": expected_version,
            "before": before_status,
            "after": property_obj.status,
        },
    )

    PlanningEvent.objects.create(
        recipient=property_obj.owner,
        event_key=f"property.moderation:{decision.id}",
        destination={
            "action_type": "view_property",
            "property_id": str(property_obj.id),
        },
    )

    logger.info(f"Property {property_obj.id} hidden/blocked by moderator {reviewer.email}")
    return property_obj
