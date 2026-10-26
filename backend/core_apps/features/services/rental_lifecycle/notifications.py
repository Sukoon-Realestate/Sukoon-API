"""Reuse the planning outbox; no push or provider calls in domain transactions."""

from ...planning_models import PlanningEvent


def record_rental_event(
    item, recipients, action="rental.updated", destination="open_rental_deal"
):
    prop = getattr(item, "property", None) or getattr(
        getattr(item, "lease", None), "property", None
    )
    owner_id = getattr(item, "owner_id", None) or getattr(prop, "owner_id", None)
    interest = getattr(item, "interest", None)
    student_id = interest.tenant_id if interest and interest.academic_plan_id else None
    group_booking = destination == "open_group_booking"
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
                    **({"event_kind": action, "content_version": item.content_revision}
                       if destination == "open_rental_terms" else {}),
                    "workspace": "owner" if recipient.pk == owner_id else "student" if group_booking or recipient.pk == student_id else "individual",
                    **({identity_field: str(item.id)} if identity_field else {}),
                    **({"event_kind": action, "terms_revision": item.terms_revision} if group_booking else {}),
                }
            },
        )
