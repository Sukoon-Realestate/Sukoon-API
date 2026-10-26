"""Invalidate only pre-booking group applications whose public source changed."""

from ..planning_models import GroupProcess
from core_apps.properties.services.viewing_listing_changes import source_state


def candidates(prop):
    return (
        GroupProcess.objects.filter(property=prop, kind="application")
        .exclude(status__in=["withdrawn", "expired", "rejected", "completed"])
        .exclude(selection={})
    )


def snapshot(prop):
    return {
        str(item.selection.get("offer_id", "")): source_state(
            prop, str(item.selection.get("offer_id", ""))
        )
        for item in candidates(prop)
    }


def propagate(prop, before):
    from ..planning_group_views_parts.process_payload import invalidate_process

    differences = {}
    for offer_id, previous in before.items():
        current = source_state(prop, offer_id)
        changes = [
            {"field": key, "before": previous[key], "after": current[key]}
            for key in previous
            if previous[key] != current[key]
        ]
        if changes:
            differences[offer_id] = changes
    if not differences:
        return
    for item in candidates(prop).select_for_update().order_by("pk"):
        changes = differences.get(str(item.selection.get("offer_id", "")))
        if not changes:
            continue
        # The independent booking/negotiation phase owns its own exact units and
        # private terms. A public price edit cannot withdraw those commitments.
        if item.booking_proposals.exists():
            continue
        if (
            item.interest_id
            and item.interest.invitations.filter(
                status__in=["pending", "accepted"]
            ).exists()
        ):
            continue
        invalidate_process(
            item,
            "listing_changed",
            source_change={
                "source_revision": prop.review_revision,
                "listing_changes": changes,
            },
        )
