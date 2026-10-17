"""Exact move proposal adapter to the shared canonical rental orchestrator."""

from rest_framework.exceptions import NotFound
from ...transition_network_models import TransitionCandidate
from ..rental_phase2 import RentalConflict
from .access import candidate_for
from .projections import candidate_stale


def authorize(user, source_id):
    return candidate_for(user, source_id)


def completion_state(plan, derived_state):
    if derived_state != "completed":
        return derived_state
    if any(
        leg.lease is None or leg.lease.occupancy_status != "occupied"
        for leg in plan.legs.select_related("lease")
    ):
        return "awaiting_handover"
    return derived_state


def revalidate(plan, action="prepare"):
    try:
        candidate = TransitionCandidate.objects.get(id=plan.source_id)
    except TransitionCandidate.DoesNotExist:
        raise NotFound()
    if candidate.snapshot_digest != plan.source_digest:
        raise RentalConflict(
            "Refresh the changed move proposal.", code="snapshot_stale"
        )
    # Preparation must still use the exact fresh market and outgoing-authority
    # snapshot. Later reconciliation observes existing canonical obligations;
    # the plan's own holds cannot invalidate the source after preparation.
    if action in {"consents", "prepare"}:
        if (
            candidate_stale(candidate)
            or candidate.participants.exclude(decision="interested").exists()
        ):
            raise RentalConflict(
                "Refresh the changed move proposal.", code="snapshot_stale"
            )
        if action == "prepare":
            for participant in candidate.participants.select_related("intent__lease"):
                lease = participant.intent.lease
                if lease.status != "ended" or lease.occupancy_status != "returned":
                    raise RentalConflict(
                        "Confirm the outgoing handover before reserving linked accommodation.",
                        code="physical_release_requires_confirmation",
                    )
    return candidate


def create(request, candidate):
    from ..advanced_execution.plans import create_plan

    if request.data.get(
        "snapshot_digest"
    ) != candidate.snapshot_digest or candidate_stale(candidate):
        raise RentalConflict(
            "Refresh the changed move proposal.", code="snapshot_stale"
        )
    if candidate.participants.exclude(decision="interested").exists():
        raise RentalConflict(
            "Every participant must express interest in this move proposal.",
            code="participant_consent_required",
        )
    participants = {
        str(row.intent.id): row
        for row in candidate.participants.select_related("intent__lease", "user")
    }
    legs = []
    for proposed in candidate.snapshot["legs"]:
        source = proposed["source"]
        participant = participants[proposed["intent_id"]]
        legs.append(
            {
                "key": proposed["intent_id"],
                "property_id": source["selection"]["property_id"],
                "tenant_id": str(participant.user.id),
                "owner_id": source["owner_id"],
                "selection": source["selection"],
                "starts_on": proposed["start_on"],
                "ends_on_exclusive": proposed["end_on"],
                "rent_minor": source["rent_minor"],
                "deposit_minor": source["deposit_minor"],
                "outgoing_lease_id": str(participant.intent.lease.id),
                "metadata": {"occupants": 1, "gap_days": proposed["gap_days"]},
            }
        )
    return create_plan(
        request.user,
        source_kind="transition",
        source_id=candidate.id,
        source_revision=candidate.revision,
        source_digest=candidate.snapshot_digest,
        mode="conditional_package",
        legs=legs,
        context={
            "kind": candidate.snapshot.get("kind", "cycle"),
            "physical_release_required": True,
            "financial_closure_separate": True,
        },
    )
