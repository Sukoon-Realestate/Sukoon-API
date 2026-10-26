"""Executive measures from current records; unavailable history stays unavailable."""

import logging
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from core_apps.properties.models import Property
from core_apps.admin_api.models import KYCSubmission, UserReport
from core_apps.properties.models.visit import PropertyVisit

logger = logging.getLogger(__name__)
User = get_user_model()


def get_executive_dashboard_stats():
    from .get_dashboard_overview_stats import get_dashboard_overview_stats

    now = timezone.now()
    today = timezone.localdate(now) if timezone.is_aware(now) else now.date()
    total_users = User.objects.count()
    landlords = User.objects.filter(properties__isnull=False).distinct().count()
    pending = KYCSubmission.objects.filter(
        status=KYCSubmission.Status.PENDING, superseded_at__isnull=True
    ).count()
    values = [
        ("الحسابات المفعّلة", User.objects.filter(is_active=True).count(), "users"),
        (
            "العقارات المعتمدة",
            Property.objects.filter(status=Property.Status.VERIFIED).count(),
            "building",
        ),
        (
            "طلبات الزيارة اليوم",
            PropertyVisit.objects.filter(
                created_at__date=today, created_at__lt=now
            ).count(),
            "calendar",
        ),
        ("توثيق معلق", pending, "clock"),
        (
            "بلاغات مفتوحة",
            UserReport.objects.filter(status=UserReport.Status.ACTIVE).count(),
            "alert",
        ),
    ]
    metrics = [
        {
            "title": title,
            "value": f"{count:,}",
            "change": "غير متاح",
            "isPositive": None,
            "icon": icon,
        }
        for title, count, icon in values
    ]
    registrations, reports = [], []
    for offset in range(30):
        day = today - timedelta(days=29 - offset)
        common = {
            "day": offset + 1,
            "date": day.isoformat(),
            "label": day.isoformat(),
            "isCurrent": day == today,
        }
        registrations.append(
            {
                **common,
                "value": User.objects.filter(
                    date_joined__date=day, date_joined__lt=now
                ).count(),
            }
        )
        reports.append(
            {
                **common,
                "value": UserReport.objects.filter(
                    created_at__date=day, created_at__lt=now
                ).count(),
            }
        )
    return {
        "executiveMetrics": metrics,
        "monthlyUserChartData": registrations,
        "reportTrendData": reports,
        "period": {
            "from": (today - timedelta(days=29)).isoformat(),
            "through": today.isoformat(),
            "measured_at": now.isoformat(),
        },
        "userDistribution": {
            "total": total_users,
            "tenants": total_users - landlords,
            "landlords": landlords,
            "verified": User.objects.filter(is_verified=True).count(),
            "pending": pending,
            "suspended": User.objects.filter(is_active=False).count(),
        },
        "executiveActivities": get_dashboard_overview_stats()["recent_activities"],
    }


def _format_time_ago(dt):
    if not dt:
        return "الآن"
    delta = timezone.now() - dt
    if delta.days > 1:
        return f"منذ {delta.days} يوم"
    if delta.days == 1:
        return "أمس"
    hours = delta.seconds // 3600
    if hours > 0:
        return f"منذ {hours} ساعة"
    mins = delta.seconds // 60
    if mins > 0:
        return f"منذ {mins} دقيقة"
    return "منذ لحظات"
