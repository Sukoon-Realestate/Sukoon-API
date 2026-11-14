"""Final-settlement read projection shared by money commands and transport."""

from .money_projection import _money
from .cycle_permissions import cycle_actions
from .settlement_notes import history_payload, notes_payload


def settlement_payload(item, user=None):
    from core_apps.features.services.settlements_parts.prepare_settlement import (
        settlement_precondition_error,
    )
    from core_apps.features.services.billing_sources import source_invoices

    error = settlement_precondition_error(item.lease)
    return {
        "billing_invoices": source_invoices("settlement", item.id),
        "allowed_actions": cycle_actions(user, item),
        "blocking_reasons": [error[1]] if error else [],
        "id": str(item.id) if item.id else None,
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "status": item.status,
        "lines": item.lines,
        "rent_balance": _money(item.rent_balance_minor),
        "deposit_to_return": _money(item.deposit_to_return_minor),
        "refund_due": _money(item.refund_due_minor),
        "total_due": _money(item.total_due_minor),
        "accepted_by": item.accepted_by,
        "disputed_item_ids": item.disputed_item_ids,
        "execution_status": item.execution_status,
        "execution_plan": item.execution_plan,
        "executed_at": item.executed_at.isoformat() if item.executed_at else None,
        "history": history_payload(item),
        "notes": notes_payload(item),
    }


__all__ = ["settlement_payload"]
