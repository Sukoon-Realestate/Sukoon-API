import logging
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError, NotFound
from core_apps.admin_api.models import UserReport
from core_apps.admin_api.services.user_service import suspend_user

logger = logging.getLogger(__name__)


def get_reports_queryset():
    """
    Returns optimized queryset of user reports for administrative review.
    """
    return (
        UserReport.objects.select_related("reported_user", "reporter", "reviewed_by")
        .order_by("-created_at")
    )


@transaction.atomic
def take_report_action(report_id, action, reviewer, notes=""):
    """
    Executes an administrative resolution action on a user report.
    """
    try:
        report = UserReport.objects.select_related("reported_user").get(id=report_id)
    except (UserReport.DoesNotExist, ValueError):
        raise NotFound(f"User Report with ID {report_id} was not found.")

    if action == "suspend_user":
        report.status = UserReport.Status.SUSPENDED
        suspend_user(report.reported_user.id, reviewer, reason=report.reason)
    elif action == "ban_user":
        report.status = UserReport.Status.BANNED
        suspend_user(report.reported_user.id, reviewer, reason=f"حظر نهائي: {report.reason}")
    elif action == "dismiss":
        report.status = UserReport.Status.DISMISSED
    elif action == "mark_active":
        report.status = UserReport.Status.ACTIVE
    else:
        raise ValidationError(f"Invalid action '{action}'. Valid actions: suspend_user, ban_user, dismiss, mark_active.")

    report.reviewed_by = reviewer if reviewer.is_authenticated else None
    report.reviewed_at = timezone.now()
    if notes:
        report.notes = notes
    report.save(update_fields=["status", "reviewed_by", "reviewed_at", "notes"])

    logger.info(f"Report {report.id} updated with action {action} by {reviewer.email}")
    return report
