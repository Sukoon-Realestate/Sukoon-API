"""A bounded local database check; uninstrumented services remain unknown."""

from django.db import connection
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError
from .get_audit_logs import get_audit_logs


def get_system_health():
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        database_ok = cursor.fetchone() == (1,)
    return {
        "metrics": {
            "uptime": "Unavailable",
            "uptimeSub": "No uptime telemetry connected",
            "responseTime": "Unavailable",
            "responseSub": "No API latency telemetry connected",
            "errorsToday": "Unavailable",
            "errorsSub": "No error aggregation connected",
            "dbStatus": "Reachable" if database_ok else "Unconfirmed",
            "dbSub": timezone.now().isoformat(),
        },
        "auditLogs": get_audit_logs()[:6],
        "apiPerformanceData": [],
        "internalAdminNotes": [
            "Only the database round trip was checked. CDN, backup restore, workers and provider health are unverified."
        ],
    }


def get_push_campaigns():
    return []


def send_push_notification(title, body, audience="all"):
    if not title or not str(title).strip() or not body or not str(body).strip():
        raise ValidationError("A title and body are required.")
    error = APIException(
        "Administrative broadcast delivery is unavailable: there is no durable campaign dispatcher. No recipients were notified."
    )
    error.status_code = 503
    raise error
