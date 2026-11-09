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
    *,
    expected_version=None,
    request_key=None,
):
    """Legacy moderation-queue "delete": a canonical ``block`` decision (A6-01).

    Delegates to properties.services.moderation.decide, so independent review,
    retirement/blocked conflicts, the decision record, audit and planning events
    and idempotent replay are the canonical ones (emitted exactly once). This alias
    additionally keeps its sensitive-access requirement.

    Clients that send ``expected_version`` and an ``Idempotency-Key`` get the full
    stale-command protection. The existing admin client sends neither; for it the
    version observed under the property lock is used and the operation key is
    derived from the review revision, so a repeated submit replays the first
    decision instead of applying a second one.
    """
    from core_apps.admin_api.permissions import require_staff_actor
    from core_apps.users.services.totp import require_sensitive_access
    from core_apps.properties.services.moderation import decide, version
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
    except (Property.DoesNotExist, NotFound, ValueError, InvalidIdentifier):
        raise NotFound(f"Property with ID {property_id} was not found.")

    if not expected_version:
        expected_version = version(property_obj)
    if not request_key:
        request_key = f"legacy-moderation-block:{property_obj.review_revision}"
    result, code, replayed = decide(
        property_obj.id,
        reviewer=reviewer,
        action="block",
        expected_version=expected_version,
        request_key=request_key,
        reason=reason,
        internal_note=internal_note
        or f"Removed via moderation delete route by {reviewer.email}",
    )
    logger.info("Property %s blocked via legacy moderation route", property_obj.id)
    return result, code, replayed
