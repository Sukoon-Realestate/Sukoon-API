"""Compact recovery carries identity and current state; history stays on paged GET."""

from rest_framework.exceptions import ValidationError


def compact_requested(request):
    value = request.query_params.get("receipt", "full")
    if value not in {"full", "compact"}:
        raise ValidationError({"receipt": "Use full or compact."})
    return value == "compact"


def ticket_receipt(ticket):
    return {
        "id": str(ticket.id),
        "reference": ticket.reference,
        "revision": ticket.revision,
        "status": ticket.status,
        "workspace": ticket.workspace,
        "subject": ticket.subject,
        "category": ticket.category,
    }
