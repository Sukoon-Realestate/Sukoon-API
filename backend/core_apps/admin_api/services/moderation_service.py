import logging
from django.core.exceptions import ValidationError as InvalidIdentifier
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
def delete_moderation_item(
    property_id,
    reviewer,
    reason="تم حذف وإخفاء المحتوى المخالف بواسطة المشرف",
    internal_note="",
):
    """
    Hides/removes flagged property content from the platform while enforcing
    canonical moderation invariants, sensitive-access, independent-review, and audit logs.
    """
    from core_apps.admin_api.permissions import require_staff_actor
    from core_apps.users.services.totp import require_sensitive_access
    from rest_framework.exceptions import PermissionDenied
    from core_apps.features.services.rental_phase2 import RentalConflict
    from core_apps.properties.models import PropertyModerationDecision
    from core_apps.features.models import RentalAuditEvent
    from core_apps.features.planning_models import PlanningEvent
    from core_apps.properties.services.moderation import version
    from core_apps.admin_api.services.property_service_parts.get_admin_properties_queryset import (
        _get_property_by_identifier,
    )

    reviewer = require_staff_actor(
        reviewer, {"system_owner", "main_admin", "property_reviewer"}, lock=True
    )
    require_sensitive_access(reviewer)

    try:
        found = _get_property_by_identifier(property_id)
        property_obj = Property.objects.select_for_update().get(pk=found.pk)
    except (Property.DoesNotExist, NotFound, ValueError):
        raise NotFound(f"Property with ID {property_id} was not found.")

    if property_obj.owner_id == reviewer.pk:
        raise PermissionDenied("A listing requires independent moderation.")

    if property_obj.retired_at:
        raise RentalConflict(
            "Retired inventory cannot be republished or altered.",
            code="inventory_retired",
        )

    current_version = version(property_obj)
    before_status = property_obj.status

    # Record canonical moderation decision
    decision = PropertyModerationDecision.objects.create(
        property=property_obj,
        reviewer=reviewer,
        source_revision=property_obj.review_revision,
        source_version=current_version,
        action="block",
        public_reason=reason,
        internal_note=internal_note or f"Removed via moderation delete route by {reviewer.email}",
    )

    property_obj.status = Property.Status.HIDDEN
    property_obj.is_verified = False
    property_obj.moderation_blocked = True
    property_obj.moderation_reason = reason
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
        reason=reason,
        metadata={
            "decision_id": str(decision.id),
            "version": current_version,
            "before": before_status,
            "after": property_obj.status,
            "channel": "moderation_queue",
        },
    )

    PlanningEvent.objects.create(
        recipient=property_obj.owner,
        event_key=f"property.moderation:{decision.id}",
        destination={
            "action_type": "view_property",
            "property_id": str(property_obj.id),
            "target_id": str(property_obj.id),
            "workspace": "owner",
            "revision": property_obj.review_revision,
            "event_kind": "property_review_changed",
            "schema_version": "1",
        },
    )

    logger.info(f"Property {property_obj.id} hidden and blocked by moderator {reviewer.email}")
    return property_obj
