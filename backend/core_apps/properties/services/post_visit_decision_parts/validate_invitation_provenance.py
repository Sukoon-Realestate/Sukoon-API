"""Post visit decision: validate invitation provenance."""

from .linked_invitation import DecisionConflict


def validate_invitation_provenance(invitation):
    """Defend draft creation too; historical and independent origins stay valid."""
    if invitation.provenance_version == "group_booking_v1":
        from core_apps.features.models import GroupBookingParticipant
        from core_apps.features.services.rental_lifecycle.group_bookings import (
            current_roster,
        )

        participant = (
            GroupBookingParticipant.objects.filter(invitation=invitation)
            .select_related("proposal")
            .first()
        )
        if (
            not participant
            or participant.consent_status != "accepted"
            or participant.tenant_id != invitation.tenant_id
            or participant.proposal.owner_id != invitation.owner_id
            or participant.proposal.property_id != invitation.property_id
            or participant.selection_snapshot != invitation.offer_snapshot
            or not current_roster(participant.proposal)
            or participant.proposal.terms_digest
            != invitation.eligibility_snapshot.get("terms_digest")
        ):
            raise DecisionConflict(
                "The booking participant or consent has changed.", "source_mismatch"
            )
        return
    if invitation.provenance_version == "historical_v0":
        return
    if (
        invitation.provenance_version == "independent_interest_v1"
        and invitation.interest_id
    ):
        return
    if not invitation.source_visit_id or not invitation.source_decision_id:
        raise DecisionConflict(
            "The invitation has no valid source decision.", "source_mismatch"
        )
    decision = invitation.source_decision
    visit = invitation.source_visit
    if (
        decision.visit_id != visit.pk
        or decision.value != "proceed"
        or decision.tenant_id != invitation.tenant_id
        or decision.owner_id != invitation.owner_id
        or visit.property_id != invitation.property_id
        or (visit.offer_id and invitation.offer_id != visit.offer_id)
    ):
        raise DecisionConflict(
            "The invitation source no longer matches.", "source_mismatch"
        )
