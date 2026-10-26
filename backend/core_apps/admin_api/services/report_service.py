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

    if hasattr(report, 'chat_case'):
        raise ValidationError('Rental chat cases require the versioned policy review endpoint.')
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


# * Report and Support Metrics Services

def get_report_metrics():
    """
    Returns aggregated counts for user reports by status.
    """
    active_count = UserReport.objects.filter(status=UserReport.Status.ACTIVE).count()
    suspended_count = UserReport.objects.filter(status=UserReport.Status.SUSPENDED).count()
    banned_count = UserReport.objects.filter(status=UserReport.Status.BANNED).count()
    dismissed_count = UserReport.objects.filter(status=UserReport.Status.DISMISSED).count()
    total_count = UserReport.objects.count()

    return {
        "active": active_count,
        "suspended": suspended_count,
        "banned": banned_count,
        "dismissed": dismissed_count,
        "total": total_count,
    }


def get_support_tickets_queryset():
    from core_apps.support.models import Ticket
    return Ticket.objects.select_related("user", "assigned_to").order_by("-updated_at", "-id")


def get_support_metrics():
    from core_apps.support.models import Ticket
    from django.db.models import Avg, F
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tickets = Ticket.objects.all()
    duration = tickets.filter(resolved_at__isnull=False).aggregate(
        duration=Avg(F("resolved_at") - F("created_at"))
    )["duration"]
    return {
        "avgResolutionTime": f"{duration.total_seconds() / 3600:.1f}h" if duration else "غير متاح",
        "solvedToday": tickets.filter(status__in=["resolved", "closed"], resolved_at__gte=today_start).count(),
        "inProgress": tickets.filter(status="in_progress").count(),
        "openTickets": tickets.filter(status="open").count(),
        "escalated": tickets.filter(escalated=True, status__in=["open", "in_progress"]).count(),
    }


def get_reports_overview_stats():
    """
    Returns aggregated stats and recent tickets for the reports & tickets overview page.
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    active_disputes = UserReport.objects.filter(
        status=UserReport.Status.ACTIVE,
        reason_type__in=["fraud", "misleading", "other"],
    ).count()

    solved_today = UserReport.objects.filter(
        status__in=[UserReport.Status.DISMISSED, UserReport.Status.BANNED, UserReport.Status.SUSPENDED],
        reviewed_at__gte=today_start,
        reviewed_at__lte=now,
    ).count()

    open_tickets = UserReport.objects.filter(
        status=UserReport.Status.ACTIVE,
    ).count()

    # ? Dispute reasons distribution from database
    reason_counts = {
        "fraud": UserReport.objects.filter(reason_type="fraud").count(),
        "misleading": UserReport.objects.filter(reason_type="misleading").count(),
        "spam": UserReport.objects.filter(reason_type="spam").count(),
        "abusive": UserReport.objects.filter(reason_type="abusive").count(),
        "other": UserReport.objects.filter(reason_type="other").count(),
    }

    dispute_reasons = [
        {"title": "رد الأمانة والاحتيال", "count": reason_counts["fraud"], "color": "bg-rose-500"},
        {"title": "دقة المعلومات والوصف", "count": reason_counts["misleading"], "color": "bg-amber-500"},
        {"title": "إساءة وسلوك غير لائق", "count": reason_counts["abusive"], "color": "bg-blue-500"},
        {"title": "إعلانات مزعجة وتكرار", "count": reason_counts["spam"], "color": "bg-teal-500"},
        {"title": "أسباب أخرى", "count": reason_counts["other"], "color": "bg-slate-500"},
    ]

    # ? Recent property visits for booking log
    from core_apps.properties.models.visit import PropertyVisit
    recent_visits_qs = PropertyVisit.objects.filter(created_at__lte=now).select_related("property", "tenant").order_by("-created_at")[:6]
    booking_log = []
    for visit in recent_visits_qs:
        booking_log.append({
            "id": str(visit.id),
            "title": visit.property.title,
            "status": visit.get_status_display(),
        })

    return {
        "avgResolutionTime": "غير متاح",
        "measured_at": now.isoformat(),
        "activeDisputes": active_disputes,
        "solvedToday": solved_today,
        "openTickets": open_tickets,
        "disputeReasons": dispute_reasons,
        "bookingLog": booking_log,
    }
