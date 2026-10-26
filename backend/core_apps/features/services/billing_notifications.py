"""Purchase outcomes retain their original invoice and presentation workspace."""

from django.db.models import Q
from uuid import UUID
from rest_framework.exceptions import NotFound, ValidationError

from ..planning_models import PlanningEvent

EVENT_KIND = "purchase_fulfilled"
PURPOSES = {"subscription", "advertising", "promotion"}


def purchase_workspace(body):
    expected = (
        "company"
        if body.get("organization_id")
        else ("owner" if body["workspace"] == "owner" else "individual")
    )
    workspace = body.get("notification_workspace") or expected
    allowed = {"individual", "student"} if expected == "individual" else {expected}
    if workspace not in allowed:
        raise ValidationError(
            {"notification_workspace": "The workspace does not match this purchase."}
        )
    return workspace


def invoice_workspace(invoice):
    return purchase_workspace(
        {
            "organization_id": invoice.organization_id,
            "workspace": invoice.workspace,
            "notification_workspace": invoice.purchase_snapshot.get(
                "notification_workspace"
            ),
        }
    )


def record_fulfilled(invoice, attempt):
    if (
        invoice.purpose not in PURPOSES
        or invoice.status != "paid"
        or attempt.payment_status != "captured"
    ):
        return
    job = getattr(invoice, "fulfillment", None)
    if job and job.case_id:
        # The existing case owns its recovery notice and invoice shortcut.
        return
    recipients = [attempt.payer_id]
    if invoice.organization_id:
        recipients = (
            invoice.organization.memberships.filter(
                is_active=True, user__is_active=True
            )
            .filter(Q(is_admin=True) | Q(can_execute_payments=True))
            .values_list("user_id", flat=True)
        )
    destination = {
        "schema_version": "1",
        "action_type": "open_purchase_invoice",
        "event_kind": EVENT_KIND,
        "target_id": str(invoice.id),
        "invoice_id": str(invoice.id),
        "workspace": invoice_workspace(invoice),
        "revision": invoice.revision,
        "payment_attempt_id": str(attempt.id),
    }
    if invoice.organization_id:
        destination["company_id"] = str(invoice.organization.id)
    for identity in set(recipients):
        PlanningEvent.objects.get_or_create(
            recipient_id=identity,
            event_key=f"purchase.fulfilled:{invoice.id}",
            defaults={"destination": destination},
        )


def authorize(user, destination):
    from .billing_invoices import authorized_invoice

    if (
        destination.get("event_kind") != EVENT_KIND
        or destination.get("action_type") != "open_purchase_invoice"
    ):
        raise NotFound()
    try:
        UUID(str(destination.get("target_id")))
        UUID(str(destination.get("payment_attempt_id")))
    except (ValueError, TypeError, AttributeError) as exc:
        raise NotFound() from exc
    invoice = authorized_invoice(user, destination.get("target_id"))
    company = str(invoice.organization.id) if invoice.organization_id else ""
    if (
        invoice.purpose not in PURPOSES
        or destination.get("invoice_id") != str(invoice.id)
        or destination.get("workspace") != invoice_workspace(invoice)
        or (destination.get("company_id") or "") != company
        or not invoice.payment_attempts.filter(
            id=destination.get("payment_attempt_id"), payment_status="captured"
        ).exists()
    ):
        raise NotFound()
    return {
        "title": "اكتمل تفعيل الخدمة / Service activated",
        "body": "افتح الفاتورة الأصلية لمراجعة الإيصال والحالة الحالية للخدمة. / Open the original invoice for its receipt and current service status.",
        "category": "billing",
        "notification_type": "general",
    }
