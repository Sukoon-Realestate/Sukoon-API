"""Reuse the planning outbox; no push or provider calls in domain transactions."""

from ...planning_models import PlanningEvent


def record_rental_event(
    item, recipients, action="rental.updated", destination="open_rental_deal"
):
    prop = getattr(item, "property", None) or getattr(
        getattr(item, "lease", None), "property", None
    )
    owner_id = getattr(item, "owner_id", None) or getattr(prop, "owner_id", None)
    identity_field = {
        "open_rental_interest": "rental_interest_id",
        "open_rental_terms": "terms_proposal_id",
    }.get(destination)
    for recipient in recipients:
        PlanningEvent.objects.get_or_create(
            recipient=recipient,
            event_key=f"{action}:{item.id}:{getattr(item, 'revision', 1)}",
            defaults={
                "destination": {
                    "action_type": destination,
                    "target_id": str(item.id),
                    "revision": getattr(item, "revision", 1),
                    "rental_lifecycle": True,
                    "workspace": "owner" if recipient.pk == owner_id else "tenant",
                    **({identity_field: str(item.id)} if identity_field else {}),
                }
            },
        )
