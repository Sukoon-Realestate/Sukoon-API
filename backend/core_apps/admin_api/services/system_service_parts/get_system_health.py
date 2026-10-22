"""A bounded local database check; uninstrumented services remain unknown."""

from django.db import connection
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError
from .get_audit_logs import get_audit_logs


def get_system_health():
    from core_apps.common.runtime_metrics import snapshot, evaluate_incidents
    from core_apps.common.models import RuntimeIncident
    report = snapshot()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            database_ok = cursor.fetchone() == (1,)
    except Exception:
        database_ok = False
    incidents = []
    if database_ok:
        # An unavailable worker cannot run its own monitor task. An authorized
        # dashboard read also records the current observation, without running
        # or replaying any business task.
        evaluate_incidents(report)
        incidents = list(RuntimeIncident.objects.filter(occurrences__gt=0).values(
            "code", "state", "occurrences", "opened_at", "last_seen_at", "resolved_at"
        ))
    return {
        "metrics": {
            "uptime": "Unavailable", "uptimeSub": "No long-term uptime measurement",
            "responseTime": f"{report['average_ms']:.1f} ms" if report['average_ms'] is not None else "Unavailable",
            "responseSub": f"Observed window: {report['window_seconds']} seconds",
            "errorsToday": str(report['server_errors']) if report['server_errors'] is not None else "Unavailable",
            "errorsSub": "5xx errors in the measured window; not a daily total",
            "dbStatus": "Reachable" if database_ok else "Unconfirmed", "dbSub": timezone.now().isoformat(),
        },
        "telemetry": report,
        "incidents": incidents,
        "auditLogs": get_audit_logs()[:6], "apiPerformanceData": [],
        "internalAdminNotes": ["Missing samples remain unknown. Provider delivery and backup restoration require separate evidence."],
    }


def get_push_campaigns():
    from core_apps.admin_api.models import PushCampaign
    from core_apps.admin_api.services.push_campaigns import payload
    return [payload(item) for item in PushCampaign.objects.order_by("-created_at")[:100]]


def send_push_notification(title, body, audience="all"):
    if not title or not str(title).strip() or not body or not str(body).strip():
        raise ValidationError("A title and body are required.")
    error = APIException(
        "Direct broadcast is disabled. Create a campaign preview and explicitly confirm its audience and revision. No recipients were notified."
    )
    error.status_code = 503
    raise error
