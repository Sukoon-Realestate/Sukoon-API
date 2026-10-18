"""Render persisted decisions only; current entity state is not an audit event."""

from core_apps.admin_api.models import (
    KYCSubmission,
    UserReport,
    StaffAuthorityAudit,
    PlatformPreferenceAudit,
)


def get_audit_logs(type_filter=None, search=None):
    logs = []

    def add(identifier, at, action, kind, target, actor):
        if not at:
            return
        logs.append(
            {
                "id": identifier,
                "time": at.isoformat(),
                "action": action,
                "typeBadge": kind,
                "target": target,
                "operator": actor.email if actor else "Unknown historical actor",
            }
        )

    for item in (
        KYCSubmission.objects.filter(reviewed_at__isnull=False)
        .select_related("reviewer")
        .order_by("-reviewed_at")[:100]
    ):
        add(
            f"kyc-{item.id}",
            item.reviewed_at,
            f"Identity decision: {item.status}",
            "KYC",
            str(item.profile_id),
            item.reviewer,
        )
    for item in StaffAuthorityAudit.objects.select_related("actor").order_by(
        "-created_at"
    )[:100]:
        add(
            f"staff-{item.pk}",
            item.created_at,
            f"Staff authority: {item.action}",
            "دور",
            str(item.target_id),
            item.actor,
        )
    for item in PlatformPreferenceAudit.objects.select_related("actor").order_by(
        "-created_at"
    )[:100]:
        add(
            f"settings-{item.pk}",
            item.created_at,
            f"Dashboard preferences revision {item.revision}",
            "نظام",
            "platform preferences",
            item.actor,
        )
    for item in (
        UserReport.objects.filter(reviewed_by__isnull=False)
        .select_related("reviewed_by")
        .order_by("-updated_at")[:100]
    ):
        add(
            f"report-{item.id}",
            item.updated_at,
            f"Report decision: {item.status}",
            "بلاغ",
            str(item.reported_user_id),
            item.reviewed_by,
        )
    from core_apps.features.models import RentalAuditEvent

    for item in (
        RentalAuditEvent.objects.filter(subject_kind="property")
        .select_related("actor")
        .order_by("-created_at")[:100]
    ):
        add(
            f"property-{item.id}",
            item.created_at,
            item.action,
            "عقار",
            str(item.subject_id),
            item.actor,
        )
    mapping = {
        "kyc": "KYC",
        "roles": "دور",
        "system": "نظام",
        "reports": "بلاغ",
        "props": "عقار",
        "users": "مستخدم",
        "support": "دعم",
    }
    if type_filter and type_filter != "all":
        logs = [
            row
            for row in logs
            if row["typeBadge"] == mapping.get(type_filter, type_filter)
        ]
    if search:
        logs = [
            row
            for row in logs
            if search.casefold() in " ".join(row.values()).casefold()
        ]
    return sorted(logs, key=lambda row: row["time"], reverse=True)
