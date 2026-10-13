"""System service: get system health."""

from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .logger import _PUSH_CAMPAIGNS
from .get_audit_logs import get_audit_logs


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
