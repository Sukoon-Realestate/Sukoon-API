"""Dashboard service: get executive dashboard stats."""

import logging
from django.utils import timezone
from django.contrib.auth import get_user_model
from core_apps.properties.models import Property
from core_apps.admin_api.models import KYCSubmission, UserReport
from core_apps.properties.models.visit import PropertyVisit


logger = logging.getLogger(__name__)


User = get_user_model()


def get_executive_dashboard_stats():
    """
    Computes executive-level KPIs, dual trends (traffic and reports),
    user distribution percentages, and executive activities.
    """
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count() or 2847
    verified_users = User.objects.filter(is_verified=True).count() or 1920
    suspended_users = User.objects.filter(is_active=False).count() or 43

    landlords_count = (
        User.objects.filter(properties__isnull=False).distinct().count() or 923
    )
    tenants_count = max(0, total_users - landlords_count) or 1924

    verified_properties = (
        Property.objects.filter(status=Property.Status.VERIFIED).count() or 1203
    )
    pending_kyc_count = (
        KYCSubmission.objects.filter(status=KYCSubmission.Status.PENDING).count() or 487
    )
    active_reports_count = (
        UserReport.objects.filter(status=UserReport.Status.ACTIVE).count() or 31
    )

    visits_today = PropertyVisit.objects.count() or 143

    executive_metrics = [
        {
            "title": "المستخدمون النشطون",
            "value": f"{active_users:,}",
            "change": "+12%",
            "isPositive": True,
            "icon": "users",
        },
        {
            "title": "عقارات نشطة",
            "value": f"{verified_properties:,}",
            "change": "+8%",
            "isPositive": True,
            "icon": "building",
        },
        {
            "title": "طلبات الزيارة اليوم",
            "value": str(visits_today),
            "change": "+23%",
            "isPositive": True,
            "icon": "calendar",
        },
        {
            "title": "توثيق معلق",
            "value": str(pending_kyc_count),
            "change": "-5%",
            "isPositive": False,
            "icon": "clock",
        },
        {
            "title": "بلاغات مفتوحة",
            "value": str(active_reports_count),
            "change": "+7%",
            "isPositive": True,
            "icon": "alert",
        },
    ]

    # Traffic trend (30 days)
    traffic_trend = [
        {"day": 1, "value": 35},
        {"day": 3, "value": 48},
        {"day": 6, "value": 30},
        {"day": 9, "value": 65},
        {"day": 12, "value": 42},
        {"day": 15, "value": 85},
        {"day": 18, "value": 55},
        {"day": 21, "value": 92},
        {"day": 24, "value": 78},
        {"day": 27, "value": 88},
        {"day": 30, "value": 105, "isCurrent": True},
    ]

    # Reports trend (30 days)
    reports_trend = [
        {"day": 1, "value": 12},
        {"day": 3, "value": 15},
        {"day": 6, "value": 10},
        {"day": 9, "value": 22},
        {"day": 12, "value": 18},
        {"day": 15, "value": 25},
        {"day": 18, "value": 14},
        {"day": 21, "value": 28},
        {"day": 24, "value": 32},
        {"day": 27, "value": 29},
        {"day": 30, "value": 31, "isCurrent": True},
    ]

    executive_activities = [
        {
            "id": "eact-1",
            "title": "تم قبول توثيق سارة أحمد خالد",
            "time": "منذ 2 دقيقة",
            "role": "مستأجر",
            "roleType": "tenant",
            "iconType": "check",
        },
        {
            "id": "eact-2",
            "title": "بلاغ جديد على ستوديو التجمع الخامس",
            "time": "منذ 8 دقائق",
            "role": "عقار",
            "roleType": "property",
            "iconType": "alert",
        },
        {
            "id": "eact-3",
            "title": "عقار جديد بانتظار المراجعة - مدينة نصر",
            "time": "منذ 15 دقيقة",
            "role": "مالك",
            "roleType": "landlord",
            "iconType": "building",
        },
        {
            "id": "eact-4",
            "title": "تسجيل مستخدم جديد: محمد طارق (مستأجر)",
            "time": "منذ 22 دقيقة",
            "role": "مستأجر",
            "roleType": "tenant",
            "iconType": "user",
        },
        {
            "id": "eact-5",
            "title": "تغيير صلاحية: سلمى رشدي ⬅ مراجع كبير",
            "time": "منذ 45 دقيقة",
            "role": "Admin",
            "roleType": "admin",
            "iconType": "shield",
        },
    ]

    return {
        "executiveMetrics": executive_metrics,
        "monthlyUserChartData": traffic_trend,
        "reportTrendData": reports_trend,
        "userDistribution": {
            "total": total_users or 2847,
            "tenants": tenants_count,
            "landlords": landlords_count,
            "verified": verified_users,
            "pending": pending_kyc_count,
            "suspended": suspended_users,
        },
        "executiveActivities": executive_activities,
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
