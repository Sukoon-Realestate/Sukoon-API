"""Expiry opens the original service/receipt, never a replacement purchase."""

from uuid import UUID

from django.db.models import Q
from rest_framework.exceptions import NotFound

from ..planning_models import PlanningEvent
from .billing_notifications import invoice_workspace

EVENT_KIND = "commerce_service_expired"


def record(kind, item, invoice):
    destination = {
        "schema_version": "1",
        "event_kind": EVENT_KIND,
        "service_kind": kind,
        "service_id": str(item.id),
        "expired_at": item.ends_at.isoformat(),
        "workspace": "owner",
    }
    recipients = [item.user_id if kind == "subscription" else item.owner_id]
    if invoice:
        destination.update(
            action_type="open_purchase_invoice",
            target_id=str(invoice.id),
            invoice_id=str(invoice.id),
            workspace=invoice_workspace(invoice),
        )
        if invoice.organization_id:
            destination["company_id"] = str(invoice.organization.id)
            destination["company_role"] = "payer"
            recipients = (
                invoice.organization.memberships.filter(
                    is_active=True, user__is_active=True
                )
                .filter(Q(is_admin=True) | Q(can_execute_payments=True))
                .values_list("user_id", flat=True)
            )
    elif kind in {"promotion", "advertising"}:
        destination.update(
            action_type="open_promotion" if kind == "promotion" else "open_banner_ad",
            target_id=str(item.id),
        )
    else:
        # Legacy services without an original invoice must not get a fabricated
        # invoice or a destination pointing at a different purchase.
        return
    for recipient in set(recipients):
        PlanningEvent.objects.get_or_create(
            recipient_id=recipient,
            event_key=f"commerce.expired:{kind}:{item.id}",
            defaults={"destination": destination},
        )


def authorize(user, destination):
    from .billing_invoices import authorized_invoice
    from .purchase_service_state import service_state
    from .commerce_expiration import MODELS

    kind = destination.get("service_kind")
    try:
        identity = UUID(str(destination.get("service_id")))
        UUID(str(destination.get("target_id")))
    except (TypeError, ValueError, AttributeError) as exc:
        raise NotFound() from exc
    if destination.get("event_kind") != EVENT_KIND or kind not in MODELS:
        raise NotFound()
    item = MODELS[kind].objects.filter(id=identity).first()
    if (
        not item
        or not item.expiration_processed_at
        or destination.get("expired_at") != item.ends_at.isoformat()
    ):
        raise NotFound()
    if destination.get("action_type") == "open_purchase_invoice":
        invoice = authorized_invoice(user, destination["target_id"])
        state = service_state(invoice)
        if (
            not state
            or state["id"] != str(identity)
            or invoice.purpose != kind
            or destination.get("invoice_id") != str(invoice.id)
            or destination.get("workspace") != invoice_workspace(invoice)
            or (destination.get("company_id") or "")
            != (str(invoice.organization.id) if invoice.organization_id else "")
        ):
            raise NotFound()
    elif (
        kind not in {"promotion", "advertising"}
        or destination.get("action_type")
        != ("open_promotion" if kind == "promotion" else "open_banner_ad")
        or destination.get("target_id") != str(identity)
        or item.owner_id != user.pk
        or destination.get("workspace") != "owner"
        or destination.get("company_id")
        or destination.get("invoice_id")
    ):
        raise NotFound()
    return {
        "title": "انتهت مدة الخدمة / Service period ended",
        "body": "راجع الخدمة الأصلية وتاريخها وحالتها الحالية. / Review the original service, its dates and current status.",
        "category": "billing",
        "notification_type": "general",
    }
