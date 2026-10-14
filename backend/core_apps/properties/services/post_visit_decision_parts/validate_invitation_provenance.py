"""Post visit decision: validate invitation provenance."""

from .linked_invitation import DecisionConflict


def validate_invitation_provenance(invitation):
    """Defend draft creation too; historical and independent origins stay valid."""
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
