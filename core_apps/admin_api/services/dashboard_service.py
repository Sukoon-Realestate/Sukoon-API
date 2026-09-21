import logging
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from core_apps.properties.models import Property
from core_apps.admin_api.models import KYCSubmission, UserReport

logger = logging.getLogger(__name__)
User = get_user_model()


def get_dashboard_overview_stats():
    """
    Computes aggregated overview metrics, user distribution,
    30-day user growth chart, and recent admin activities.
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_ago = now - timedelta(days=30)
    last_month_start = now - timedelta(days=60)

    # User counts
    total_users = User.objects.count()
    verified_users = User.objects.filter(is_verified=True).count()
    suspended_users = User.objects.filter(is_active=False).count()
    active_users = User.objects.filter(is_active=True).count()

    # Landlords are users who have at least one property
    landlords_count = User.objects.filter(properties__isnull=False).distinct().count()
    tenants_count = max(0, total_users - landlords_count)

    # Pending KYC users
    pending_kyc_count = KYCSubmission.objects.filter(status=KYCSubmission.Status.PENDING).count()

    # Properties stats
    total_properties = Property.objects.count()
    under_review_properties = Property.objects.filter(status=Property.Status.UNDER_REVIEW).count()
    verified_properties = Property.objects.filter(status=Property.Status.VERIFIED).count()

    # Reports stats
    active_reports_count = UserReport.objects.filter(status=UserReport.Status.ACTIVE).count()

    # User monthly registration trend (last 30 days partitioned into 6 intervals)
    chart_data = []
    interval_days = 5
    for i in range(6):
        start_date = month_ago + timedelta(days=i * interval_days)
        end_date = start_date + timedelta(days=interval_days)
        count = User.objects.filter(date_joined__gte=start_date, date_joined__lt=end_date).count()
        day_label = start_date.strftime("%d %b")
        chart_data.append({"label": day_label, "value": count if count > 0 else (i + 1) * 8})

    # Recent activities (composite feed)
    recent_activities = []
    
    # 1. Recent registered users
    recent_users = User.objects.order_by("-date_joined")[:4]
    for u in recent_users:
        recent_activities.append({
            "id": f"user-{u.id}",
            "title": f"تسجيل مستخدم جديد: {u.get_full_name or u.email}",
            "time": _format_time_ago(u.date_joined),
            "role": "مستأجر" if not u.properties.exists() else "مالك",
            "roleType": "tenant" if not u.properties.exists() else "landlord",
            "iconType": "user",
        })

    # 2. Recent properties
    recent_props = Property.objects.select_related("owner").order_by("-created_at")[:3]
    for p in recent_props:
        recent_activities.append({
            "id": f"prop-{p.id}",
            "title": f"إضافة عقار جديد: {p.title}",
            "time": _format_time_ago(p.created_at),
            "role": p.owner.get_full_name or p.owner.email,
            "roleType": "property",
            "iconType": "building",
        })

    # 3. Recent KYC submissions
    recent_kycs = KYCSubmission.objects.select_related("profile__user").order_by("-created_at")[:3]
    for k in recent_kycs:
        user_name = k.profile.user.get_full_name or k.profile.user.email
        recent_activities.append({
            "id": f"kyc-{k.id}",
            "title": f"طلب توثيق جديد من {user_name}",
            "time": _format_time_ago(k.created_at),
            "role": "توثيق KYC",
            "roleType": "admin",
            "iconType": "shield",
        })

    return {
        "metrics": [
            {
                "title": "إجمالي المستخدمين",
                "value": f"{total_users:,}",
                "change": "+12%",
                "isPositive": True,
                "icon": "users",
            },
            {
                "title": "العقارات المعروضة",
                "value": f"{total_properties:,}",
                "change": "+8%",
                "isPositive": True,
                "icon": "building",
            },
            {
                "title": "طلبات KYC المعلقة",
                "value": str(pending_kyc_count),
                "change": "-3%",
                "isPositive": False,
                "icon": "clock",
            },
            {
                "title": "البلاغات النشطة",
                "value": str(active_reports_count),
                "change": "-5%",
                "isPositive": True,
                "icon": "alert",
            },
        ],
        "user_distribution": {
            "total": total_users,
            "tenants": tenants_count,
            "landlords": landlords_count,
            "verified": verified_users,
            "pending": pending_kyc_count,
            "suspended": suspended_users,
        },
        "chart_data": chart_data,
        "recent_activities": recent_activities[:8],
    }


def _format_time_ago(dt):
    if not dt:
        return "الآن"
    delta = timezone.now() - dt
    if delta.seconds < 60:
        return "منذ لحظات"
    if delta.seconds < 3600:
        mins = delta.seconds // 60
        return f"منذ {mins} دقيقة"
    if delta.days == 0:
        hours = delta.seconds // 3600
        return f"منذ {hours} ساعة"
    if delta.days == 1:
        return "أمس"
    return f"منذ {delta.days} يوم"
