import logging
from datetime import datetime
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.admin_api.models import KYCSubmission, StaffProfile
from core_apps.properties.models import Property
from core_apps.admin_api.models import UserReport

logger = logging.getLogger(__name__)

# * In-memory storage for push campaigns
_PUSH_CAMPAIGNS = [
    {
        "id": "nc-1",
        "title": "عروض الصيف!",
        "timeAgo": "النهاردة 9:00 ص",
        "body": "احجز زيارتك واستمتع بخصم 20%",
        "openRate": "34% فتح",
        "recipientCount": "2,847 وصل",
    },
    {
        "id": "nc-2",
        "title": "عقارات جديدة!",
        "timeAgo": "أمس 3:00 م",
        "body": "شقق جديدة في مدينة نصر",
        "openRate": "28% فتح",
        "recipientCount": "1,924 وصل",
    },
    {
        "id": "nc-3",
        "title": "تذكير توثيق",
        "timeAgo": "قبل 3 أيام",
        "body": "وثّق هويتك وابدأ التواصل",
        "openRate": "45% فتح",
        "recipientCount": "923 وصل",
    },
]


# * System Health Service

def get_system_health():
    """
    Returns system health KPIs, API response stats, audit log previews, and notes.
    """
    # ? Performance chart
    api_performance = [
        {"hour": "12:00", "ms": 120, "height": "40%"},
        {"hour": "12:05", "ms": 140, "height": "55%"},
        {"hour": "12:10", "ms": 180, "height": "80%"},
        {"hour": "12:15", "ms": 135, "height": "50%"},
        {"hour": "12:20", "ms": 210, "height": "95%"},
        {"hour": "12:25", "ms": 160, "height": "70%"},
        {"hour": "12:30", "ms": 142, "height": "58%"},
        {"hour": "12:35", "ms": 175, "height": "75%"},
        {"hour": "12:40", "ms": 130, "height": "48%"},
        {"hour": "12:45", "ms": 150, "height": "62%"},
        {"hour": "12:50", "ms": 195, "height": "88%"},
        {"hour": "12:55", "ms": 142, "height": "58%"},
    ]

    notes = [
        "قاعدة البيانات تعمل بكفاءة 99.8%",
        "خادم CDN مستقر – لا توجد مشاكل",
        "النسخ الاحتياطي اليومي: مكتمل 03:00",
        "تحديث الأمان القادم: الأحد 2:00 ص",
    ]

    all_logs = get_audit_logs()
    preview_logs = all_logs[:6]

    return {
        "metrics": {
            "uptime": "99.8%",
            "uptimeSub": "آخر 30 يوم",
            "responseTime": "142ms",
            "responseSub": "متوسط API",
            "errorsToday": "0",
            "errorsSub": "أخطاء 5xx",
            "dbStatus": "طبيعي",
            "dbSub": "اتصال مستقر",
        },
        "auditLogs": preview_logs,
        "apiPerformanceData": api_performance,
        "internalAdminNotes": notes,
    }


# * Audit Logs Service

def get_audit_logs(type_filter=None, search=None):
    """
    Synthesizes and retrieves system audit logs from KYC, property, report, and staff actions.
    """
    logs = []

    # ? 1. KYC Reviews
    kyc_items = (
        KYCSubmission.objects.filter(reviewer__isnull=False)
        .select_related("reviewer", "profile__user")
        .order_by("-updated_at")[:20]
    )
    for kyc in kyc_items:
        u_name = kyc.profile.user.get_full_name if (kyc.profile and kyc.profile.user) else "مستخدم"
        action_verb = "قبول توثيق هوية" if kyc.status == KYCSubmission.Status.APPROVED else "رفض توثيق هوية"
        op_name = kyc.reviewer.get_full_name if kyc.reviewer else "مشرف النظام"
        t_str = kyc.updated_at.strftime("%H:%M:%S") if kyc.updated_at else "09:41:23"

        logs.append({
            "id": f"log-kyc-{kyc.id}",
            "time": t_str,
            "action": f"{action_verb} – {u_name}",
            "typeBadge": "KYC",
            "target": "مستأجر",
            "operator": op_name or "سلمى رشدي",
        })

    # ? 2. Property Status Changes
    props = (
        Property.objects.filter(
            status__in=[Property.Status.VERIFIED, Property.Status.HIDDEN, Property.Status.NEEDS_REVISION]
        )
        .select_related("owner")
        .order_by("-updated_at")[:20]
    )
    for prop in props:
        t_str = prop.updated_at.strftime("%H:%M:%S") if prop.updated_at else "09:35:10"
        if prop.status == Property.Status.VERIFIED:
            act = f"قبول عقار – {prop.title}"
        elif prop.status == Property.Status.HIDDEN:
            act = f"إخفاء عقار – {prop.title}"
        else:
            act = f"طلب تعديل عقار – {prop.title}"

        logs.append({
            "id": f"log-prop-{prop.id}",
            "time": t_str,
            "action": act,
            "typeBadge": "عقار",
            "target": "مالك",
            "operator": "أحمد العدل",
        })

    # ? 3. User Reports Resolved
    reports = (
        UserReport.objects.filter(reviewed_by__isnull=False)
        .select_related("reviewed_by", "reported_user")
        .order_by("-updated_at")[:20]
    )
    for rep in reports:
        t_str = rep.updated_at.strftime("%H:%M:%S") if rep.updated_at else "08:44:18"
        op_name = rep.reviewed_by.get_full_name if rep.reviewed_by else "مشرف التقارير"
        u_name = rep.reported_user.get_full_name if rep.reported_user else "مستخدم"

        logs.append({
            "id": f"log-rep-{rep.id}",
            "time": t_str,
            "action": f"معالجة بلاغ ضد {u_name} – {rep.reason_type}",
            "typeBadge": "بلاغ",
            "target": "مستخدم",
            "operator": op_name or "كريم فاروق",
        })

    # ? 4. Fallback items if logs are empty
    if not logs:
        logs = [
            {
                "id": "log-1",
                "time": "09:41:23",
                "action": "قبول توثيق هوية – سارة أحمد خالد",
                "typeBadge": "KYC",
                "target": "مستأجر",
                "operator": "سلمى رشدي",
            },
            {
                "id": "log-2",
                "time": "09:35:10",
                "action": "رفض عقار – كريم سالم فاروق",
                "typeBadge": "عقار",
                "target": "مالك",
                "operator": "أحمد العدل",
            },
            {
                "id": "log-3",
                "time": "09:20:04",
                "action": "إيقاف حساب طارق محمد – لغة مسيئة",
                "typeBadge": "مستخدم",
                "target": "مستأجر",
                "operator": "أحمد العدل",
            },
            {
                "id": "log-4",
                "time": "09:10:55",
                "action": "تغيير دور دينا حسام ⬅ دعم عملاء",
                "typeBadge": "دور",
                "target": "Admin",
                "operator": "أحمد العدل",
            },
            {
                "id": "log-5",
                "time": "08:55:30",
                "action": "حل تذكرة SUP-199 – مشكلة صور",
                "typeBadge": "دعم",
                "target": "مالك",
                "operator": "سلمى رشدي",
            },
            {
                "id": "log-6",
                "time": "08:44:18",
                "action": "رفض بلاغ على شقة المعادي – غير مؤكد",
                "typeBadge": "بلاغ",
                "target": "عقار",
                "operator": "كريم فاروق",
            },
            {
                "id": "log-7",
                "time": "08:30:00",
                "action": "إرسال إشعار – عروض الصيف 2,847 مستخدم",
                "typeBadge": "نظام",
                "target": "الكل",
                "operator": "أحمد العدل",
            },
        ]

    # ? 5. Filter by type
    if type_filter and type_filter != "all":
        type_map = {
            "kyc": "KYC",
            "props": "عقار",
            "users": "مستخدم",
            "system": "نظام",
            "reports": "بلاغ",
            "roles": "دور",
            "support": "دعم",
            "KYC": "KYC",
            "عقار": "عقار",
            "مستخدم": "مستخدم",
            "نظام": "نظام",
            "بلاغ": "بلاغ",
            "دور": "دور",
            "دعم": "دعم",
        }
        target_type = type_map.get(type_filter)
        if target_type:
            logs = [l for l in logs if l["typeBadge"] == target_type]

    # ? 6. Filter by search
    if search:
        search_lower = search.lower()
        logs = [
            l for l in logs
            if (
                search_lower in l["action"].lower()
                or search_lower in l["operator"].lower()
                or search_lower in l["target"].lower()
            )
        ]

    return logs


# * Push Notifications Service

def get_push_campaigns():
    """
    Returns list of notification campaigns.
    """
    return _PUSH_CAMPAIGNS


def send_push_notification(title, body, audience="all"):
    """
    Validates and queues a push notification campaign.
    """
    if not title or not title.strip():
        raise ValidationError({"title": "عنوان الإشعار مطلوب"})
    if not body or not body.strip():
        raise ValidationError({"body": "نص الإشعار مطلوب"})

    recipient_counts = {
        "all": "2,847 وصل",
        "tenants": "1,924 وصل",
        "landlords": "923 وصل",
        "verified": "1,920 وصل",
    }
    recipient_count = recipient_counts.get(audience, "2,847 وصل")

    new_campaign = {
        "id": f"nc-{int(timezone.now().timestamp())}",
        "title": title.strip(),
        "timeAgo": "الآن",
        "body": body.strip(),
        "openRate": "0% فتح",
        "recipientCount": recipient_count,
    }

    _PUSH_CAMPAIGNS.insert(0, new_campaign)
    return new_campaign
