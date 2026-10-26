"""Keep attendance consent independent of rent before a visit is dispatched."""

from django.utils import timezone
from ..planning_models import GroupProcess
from core_apps.properties.services.viewing_listing_changes import (
    source_state,
    impact_reason,
)


def candidates(prop):
    return GroupProcess.objects.filter(
        property=prop,
        kind="visit",
        visit__isnull=True,
        status__in=["collecting_consent", "ready"],
    ).exclude(selection={})


def snapshot(prop):
    return {
        str(item.selection.get("offer_id", "")): source_state(
            prop, str(item.selection.get("offer_id", ""))
        )
        for item in candidates(prop)
    }


def propagate(prop, before):
    from ..planning_group_views_parts.process_payload import invalidate_process
    from .group_process_events import record_change
    from .planning import selection_payload
    from .tenancy_invitations import resolve_offer_snapshot

    for item in candidates(prop).select_for_update().order_by("pk"):
        offer_id = str(item.selection.get("offer_id", ""))
        previous = before.get(offer_id)
        if previous is None:
            continue
        current = source_state(prop, offer_id)
        changes = [
            {"field": key, "before": value, "after": current[key]}
            for key, value in previous.items()
            if value != current[key]
        ]
        reason = impact_reason(
            current, {row["field"] for row in changes}, len(item.participant_ids)
        )
        source_change = {
            "source_revision": prop.review_revision,
            "listing_changes": changes,
        }
        if reason != "terms_changed":
            invalidate_process(item, reason, source_change=source_change)
            continue
        offer = next(
            row
            for row in prop.rental_inventory["offers"]
            if str(row.get("id")) == offer_id
        )
        _, resolved = resolve_offer_snapshot(prop, offer_id, offer["revision"])
        selected = selection_payload(resolved)
        if item.selection == selected and not changes:
            continue
        previous_selection = item.selection
        item.selection = selected
        item.revision += 1
        if changes:
            item.history.append(
                {
                    "action": "source_changed",
                    "reason_code": "visit_terms_changed",
                    "at": timezone.now().isoformat(),
                    "revision": item.revision,
                    "from_status": item.status,
                    "to_status": item.status,
                    "previous_selection": previous_selection,
                    **source_change,
                }
            )
        # This records current listing facts, not rental consent. Dispatch still
        # checks publication, current membership, explicit attendance and source.
        item.save(update_fields=["selection", "revision", "history", "updated_at"])
        if changes:
            record_change(item, item.status)
