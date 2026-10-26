"""Per-allocation source history without rewriting independent commitments."""

from collections import defaultdict
from django.utils import timezone
from ..models import GroupBookingParticipant, RentalAuditEvent
from ..planning_models import PlanningEvent
from .rental_lifecycle.common import audit
from .rental_phase2 import RentalConflict
from core_apps.properties.services.viewing_listing_changes import source_state

ACTION = "group_booking_source_changed"
MATERIAL = {
    "location",
    "accommodation",
    "capacity",
    "price_period",
    "suitable_for",
    "smoking_allowed",
    "rules",
}


def candidates(prop):
    return GroupBookingParticipant.objects.filter(
        proposal__property=prop,
        proposal__status__in=[
            "draft",
            "negotiating",
            "changes_requested",
            "awaiting_participants",
        ],
        proposal__deadline__gt=timezone.now(),
        consent_status="pending",
        invitation__isnull=True,
        lease__isnull=True,
    )


def snapshot(prop):
    return {
        offer: source_state(prop, offer)
        for offer in candidates(prop).values_list("offer_id", flat=True).distinct()
    }


def events(proposal):
    return RentalAuditEvent.objects.filter(
        subject_kind=proposal._meta.model_name,
        subject_id=proposal.id,
        action=ACTION,
    ).order_by("created_at", "pk")


def invalidated(proposal):
    return {
        row["tenant_id"]
        for event in events(proposal)
        for row in event.metadata.get("allocations", [])
        if row.get("source_review_required")
    }


def require_current(proposal, row):
    if str(row.tenant.id) in invalidated(proposal):
        raise RentalConflict(
            "This allocated accommodation changed. Review its history and withdraw the affected pending allocation before arranging new accommodation.",
            code="group_allocation_changed",
        )


def propagate(prop, before):
    differences = {}
    for offer, previous in before.items():
        current = source_state(prop, offer)
        # Agreed private commercial terms remain independent of the public price.
        changes = [
            {"field": key, "before": previous[key], "after": current[key]}
            for key in sorted(MATERIAL | {"availability"})
            if previous[key] != current[key]
        ]
        if changes:
            differences[offer] = changes
    if not differences:
        return
    proposals, affected = {}, defaultdict(list)
    # The property lock serializes consent. Avoid acquiring the group lock in
    # reverse order: immutable audit records have no FK lock on the proposal.
    for row in (
        candidates(prop)
        .filter(offer_id__in=differences)
        .select_related("proposal__application", "tenant")
    ):
        proposals[row.proposal_id] = row.proposal
        changes = differences[row.offer_id]
        affected[row.proposal_id].append(
            {
                "tenant_id": str(row.tenant.id),
                "offer_id": row.offer_id,
                "source_review_required": any(c["field"] in MATERIAL for c in changes),
                "listing_changes": changes,
            }
        )
    for identity, rows in affected.items():
        proposal = proposals[identity]
        event = audit(
            proposal,
            prop.owner,
            ACTION,
            metadata={
                "source_revision": prop.review_revision,
                "terms_revision": proposal.terms_revision,
                "allocations": rows,
            },
        )
        recipients = {proposal.owner_id, proposal.application.initiated_by_id}
        recipients.update(
            proposal.participants.filter(
                tenant__id__in=[r["tenant_id"] for r in rows]
            ).values_list("tenant_id", flat=True)
        )
        for recipient_id in recipients:
            PlanningEvent.objects.get_or_create(
                recipient_id=recipient_id,
                event_key=f"group.source:{event.id}",
                defaults={
                    "destination": {
                        "action_type": "open_group_booking",
                        "target_id": str(proposal.id),
                        "workspace": (
                            "owner" if recipient_id == proposal.owner_id else "student"
                        ),
                        "event_kind": ACTION,
                        "source_event_id": str(event.id),
                        "source_revision": prop.review_revision,
                        "terms_revision": proposal.terms_revision,
                        "rental_lifecycle": True,
                    }
                },
            )


def visible_allocations(event, actor, full):
    return [
        row
        for row in event.metadata.get("allocations", [])
        if full or row["tenant_id"] == str(actor.id)
    ]


def blockers(proposal, rows):
    from rest_framework.exceptions import APIException
    from .rental_lifecycle.group_terms import selection

    result = {}
    invalid = invalidated(proposal)
    for row in rows:
        if row.invitation_id or row.lease_id or row.consent_status != "pending":
            continue
        if str(row.tenant.id) in invalid:
            result[row.pk] = "group_allocation_changed"
            continue
        try:
            selection(proposal, row)
        except APIException:
            result[row.pk] = "group_allocation_unavailable"
    return result
