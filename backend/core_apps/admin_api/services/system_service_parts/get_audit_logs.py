"""Render persisted decisions only; current entity state is not an audit event."""

from django.db.models import Q
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

    mapping = {
        "kyc": "KYC",
        "roles": "دور",
        "system": "نظام",
        "reports": "بلاغ",
        "props": "عقار",
        "users": "مستخدم",
        "support": "دعم",
    }
    target_badge = mapping.get(str(type_filter).lower(), type_filter) if type_filter and type_filter != "all" else None

    # 1. KYC
    if target_badge is None or target_badge == "KYC":
        qs = KYCSubmission.objects.filter(reviewed_at__isnull=False).select_related("reviewer").order_by("-reviewed_at")
        if search:
            s = search.strip()
            qs = qs.filter(
                Q(reviewer__email__icontains=s)
                | Q(reviewer__first_name__icontains=s)
                | Q(reviewer__last_name__icontains=s)
                | Q(status__icontains=s)
                | Q(rejection_reason__icontains=s)
                | Q(notes__icontains=s)
            )
        for item in qs:
            add(
                f"kyc-{item.id}",
                item.reviewed_at,
                f"Identity decision: {item.status}",
                "KYC",
                str(item.profile_id),
                item.reviewer,
            )

    # 2. Staff roles
    if target_badge is None or target_badge == "دور":
        qs = StaffAuthorityAudit.objects.select_related("actor").order_by("-created_at")
        if search:
            s = search.strip()
            qs = qs.filter(
                Q(actor__email__icontains=s)
                | Q(action__icontains=s)
                | Q(reason__icontains=s)
            )
        for item in qs:
            add(
                f"staff-{item.pk}",
                item.created_at,
                f"Staff authority: {item.action}",
                "دور",
                str(item.target_id),
                item.actor,
            )

    # 3. System / Platform settings
    if target_badge is None or target_badge == "نظام":
        qs = PlatformPreferenceAudit.objects.select_related("actor").order_by("-created_at")
        if search:
            s = search.strip()
            qs = qs.filter(
                Q(actor__email__icontains=s)
                | Q(actor__first_name__icontains=s)
                | Q(actor__last_name__icontains=s)
            )
        for item in qs:
            add(
                f"settings-{item.pk}",
                item.created_at,
                f"Dashboard preferences revision {item.revision}",
                "نظام",
                "platform preferences",
                item.actor,
            )

    # 4. Reports
    if target_badge is None or target_badge == "بلاغ":
        qs = UserReport.objects.filter(reviewed_by__isnull=False).select_related("reviewed_by").order_by("-updated_at")
        if search:
            s = search.strip()
            qs = qs.filter(
                Q(reviewed_by__email__icontains=s)
                | Q(status__icontains=s)
                | Q(reason__icontains=s)
                | Q(notes__icontains=s)
            )
        for item in qs:
            add(
                f"report-{item.id}",
                item.updated_at,
                f"Report decision: {item.status}",
                "بلاغ",
                str(item.reported_user_id),
                item.reviewed_by,
            )

    # 5. Properties
    if target_badge is None or target_badge == "عقار":
        from core_apps.features.models import RentalAuditEvent

        qs = RentalAuditEvent.objects.filter(subject_kind="property").select_related("actor").order_by("-created_at")
        if search:
            s = search.strip()
            qs = qs.filter(
                Q(actor__email__icontains=s)
                | Q(action__icontains=s)
                | Q(reason__icontains=s)
            )
        for item in qs:
            add(
                f"property-{item.id}",
                item.created_at,
                item.action,
                "عقار",
                str(item.subject_id),
                item.actor,
            )

    # 6. Users (Suspension / reactivation events)
    if target_badge is None or target_badge == "مستخدم":
        qs = UserReport.objects.filter(status=UserReport.Status.SUSPENDED).select_related("reviewed_by", "reported_user").order_by("-updated_at")
        if search:
            s = search.strip()
            qs = qs.filter(
                Q(reported_user__email__icontains=s)
                | Q(reviewed_by__email__icontains=s)
                | Q(reason__icontains=s)
                | Q(notes__icontains=s)
            )
        for item in qs:
            add(
                f"user-suspend-{item.id}",
                item.updated_at,
                f"User suspension: {item.reason}",
                "مستخدم",
                str(item.reported_user_id),
                item.reviewed_by,
            )

    # 7. Support (Ticket transitions)
    if target_badge is None or target_badge == "دعم":
        try:
            from core_apps.support.models import TicketTransition

            qs = TicketTransition.objects.select_related("actor", "ticket").order_by("-created_at")
            if search:
                s = search.strip()
                qs = qs.filter(
                    Q(actor__email__icontains=s)
                    | Q(action__icontains=s)
                    | Q(reason__icontains=s)
                    | Q(ticket__reference__icontains=s)
                )
            for item in qs:
                target_ref = item.ticket.reference if getattr(item, "ticket", None) else str(item.ticket_id)
                add(
                    f"support-{item.id}",
                    item.created_at,
                    f"Ticket action: {item.action}",
                    "دعم",
                    target_ref,
                    item.actor,
                )
        except Exception:
            pass

    if target_badge:
        logs = [
            row
            for row in logs
            if row["typeBadge"] == target_badge
        ]
    if search:
        s_cf = search.casefold()
        logs = [
            row
            for row in logs
            if s_cf in " ".join(str(v) for v in row.values()).casefold()
        ]
    return sorted(logs, key=lambda row: row["time"], reverse=True)
