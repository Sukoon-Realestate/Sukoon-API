"""A projection over authoritative resources, deliberately without a deal table."""

from django.db.models import Q
from rest_framework.exceptions import NotFound
from django.utils import timezone
from ...models import (
    Lease,
    RentalInterest,
    TermsProposal,
    TenancyInvitation,
    ReservationHold,
)
from ..rental_phase2 import fingerprint
from ..rental_foundation import get_authorized_rental_subject
from ..lease_permissions import interest_actions, proposal_actions, agreement_actions
from .cases import case_queryset, case_payload
from .reservations import hold_payload


def deal_projection(user, identifier):
    source = get_authorized_rental_subject(user, identifier)
    interest = source if isinstance(source, RentalInterest) else None
    proposal = source if isinstance(source, TermsProposal) else None
    invitation = source if isinstance(source, TenancyInvitation) else None
    lease = source if isinstance(source, Lease) else None
    if isinstance(source, ReservationHold):
        proposal, lease = source.proposal, source.lease
    if lease:
        invitation = TenancyInvitation.objects.filter(lease=lease).first()
    if invitation:
        interest, proposal = invitation.interest, invitation.terms_proposal
    if proposal:
        interest = proposal.interest
    if not interest and not lease:
        raise NotFound()
    if interest and not proposal:
        proposal = interest.terms_proposals.order_by("-created_at").first()
    if interest and not invitation:
        invitation = interest.invitations.order_by("-created_at").first()
    if invitation:
        lease = invitation.lease
    prop = lease.property if lease else interest.property
    hold = (
        ReservationHold.objects.filter(
            Q(lease=lease) if lease else Q(proposal=proposal)
        )
        .order_by("-created_at")
        .first()
        if lease or proposal
        else None
    )
    resources = []
    for item, kind, actions in (
        (interest, "application", interest_actions),
        (proposal, "terms", proposal_actions),
        (invitation, "invitation", None),
        (lease, "agreement", agreement_actions),
    ):
        if item:
            resources.append(
                {
                    "id": str(item.id),
                    "kind": kind,
                    "revision": item.revision,
                    "status": item.status,
                    "allowed_actions": actions(user, item) if actions else [],
                }
            )
    terms = lease.terms if lease else (proposal.terms if proposal else {})
    timeline = (
        [
            {
                "id": str(item.id),
                "kind": item.kind,
                "label": item.label,
                "occurred_at": item.occurred_at.isoformat(),
            }
            for item in lease.timeline_events.order_by("-occurred_at")[:30]
        ]
        if lease
        else []
    )
    return {
        "id": str(source.id),
        "revision": getattr(source, "revision", 1),
        "property_id": str(prop.id),
        "property_title": prop.title,
        "selection": lease.offer_snapshot if lease else interest.offer_snapshot,
        "resources": resources,
        "terms": terms,
        "terms_digest": fingerprint(terms),
        "proposal_id": str(proposal.id) if proposal else None,
        "proposal_revision": proposal.revision if proposal else None,
        "inventory_revision": (prop.rental_inventory or {}).get("revision", 0),
        "hold": hold_payload(hold, user) if hold else None,
        "lease_id": str(lease.id) if lease else None,
        "lease_status": lease.status if lease else None,
        "occupancy_status": lease.occupancy_status if lease else None,
        "financial_closure_status": lease.financial_closure_status if lease else None,
        "waiting_for": interest.waiting_for if interest and not lease else "",
        "information_requested": interest.information_requested if interest else "",
        "applicant_response": interest.applicant_response if interest else "",
        "application_share_id": (
            str(interest.application_grant.id)
            if interest and interest.application_grant
            else None
        ),
        "response_due_at": (
            interest.response_due_at.isoformat()
            if interest and interest.response_due_at
            else None
        ),
        "timeline": timeline,
        "cases": (
            [
                case_payload(item, user)
                for item in case_queryset(user)
                .filter(lease=lease)
                .order_by("-created_at")[:10]
            ]
            if lease
            else []
        ),
        "allowed_actions": [],
        "blocking_reasons": [],
        "generated_at": timezone.now().isoformat(),
    }
