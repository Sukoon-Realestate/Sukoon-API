"""Public refund history and scoped receipts; provider details stay private."""

from django.db import connection
from rest_framework.exceptions import NotFound
from ..models import RefundRequest, RentalAuditEvent, PrivateAccessRevocation
from ..planning_models import PlanningEvent

ACTIONS = {
    "requested",
    "approved",
    "rejected",
    "authorized",
    "submitted",
    "review",
    "reauthorized",
    "failed",
    "retried",
    "succeeded",
}


def recipients(refund):
    lease = refund.lease
    denied = set(
        PrivateAccessRevocation.objects.filter(lease=lease).values_list(
            "user_id", flat=True
        )
    )
    result = []
    if lease.owner_id not in denied:
        result.append((lease.owner, "owner", "open_rental_refund", str(refund.id)))
    if lease.renter_company_id:
        from .rent_payment_recipients import recipients as company_recipients

        for user, _ in company_recipients(refund.payment_attempt.invoice):
            result.append(
                (user, "company", "open_company_tenancy", str(lease.company_tenancy.id))
            )
    elif lease.tenant_id not in denied:
        workspace = refund.payment_attempt.invoice.workspace
        result.append(
            (
                lease.tenant,
                "student" if workspace == "student" else "tenant",
                "open_rental_refund",
                str(refund.id),
            )
        )
    return [row for row in result if row[0] and row[0].is_active]


def record(refund, action, actor=None):
    if not connection.in_atomic_block or action not in ACTIONS:
        raise RuntimeError("Record the refund change inside its business transaction.")
    RentalAuditEvent.objects.get_or_create(
        subject_kind="refundrequest",
        subject_id=refund.id,
        subject_revision=refund.revision,
        action="refund_" + action,
        defaults={"actor": actor},
    )
    for user, workspace, destination, target in recipients(refund):
        PlanningEvent.objects.get_or_create(
            recipient=user,
            event_key=f"refund:{refund.id}:{refund.revision}:{action}:{workspace}",
            defaults={
                "destination": {
                    "action_type": destination,
                    "event_kind": "refund_updated",
                    "target_id": target,
                    "refund_id": str(refund.id),
                    "lease_id": str(refund.lease.id),
                    "company_id": (
                        str(refund.lease.renter_company.id)
                        if refund.lease.renter_company_id
                        else ""
                    ),
                    "workspace": workspace,
                    "revision": refund.revision,
                    "change": action,
                }
            },
        )


def authorize(event):
    data = event.destination
    refund = RefundRequest.objects.filter(
        id=data.get("refund_id"), lease__id=data.get("lease_id")
    ).first()
    if (
        not refund
        or data.get("event_kind") != "refund_updated"
        or not any(
            user.pk == event.recipient_id
            and workspace == data.get("workspace")
            and action == data.get("action_type")
            and target == data.get("target_id")
            for user, workspace, action, target in recipients(refund)
        )
    ):
        raise NotFound()
    return {
        "title": "تحديث الاسترداد / Refund update",
        "body": "راجع الحالة الحالية للطلب وتاريخ تغيّرها. / Review the current request and its history.",
    }


def history(refund):
    return [
        {
            "action": row.action.removeprefix("refund_"),
            "occurred_at": row.created_at.isoformat(),
        }
        for row in RentalAuditEvent.objects.filter(
            subject_kind="refundrequest",
            subject_id=refund.id,
            action__in=["refund_" + action for action in ACTIONS],
        ).order_by("created_at", "pk")
    ]


def attempt_history(refund):
    from ..models import PaymobRefund

    return [
        {
            "id": str(row.id),
            "current": row.current,
            "retry_of": str(row.retry_of.id) if row.retry_of_id else None,
            "status": row.status,
            "created_at": row.created_at.isoformat(),
            "submitted_at": (
                row.submitted_at.isoformat() if row.submitted_at else None
            ),
            "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
        }
        for row in PaymobRefund.objects.filter(refund=refund)
        .select_related("retry_of")
        .order_by("created_at", "pk")
    ]
