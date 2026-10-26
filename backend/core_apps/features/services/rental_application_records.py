"""Canonical record factories shared by individual and consented pair commands.

Callers own authorization, reviewed revisions, receipts and the transaction.
"""

from datetime import timedelta
from django.utils import timezone
from ..models import RentalInterest, TermsProposal, TenancyInvitation
from .rental_lifecycle.consents import record_consent


def create_interest(**values):
    return RentalInterest.objects.create(**values)


def create_terms(*, interest, owner, terms, snapshot, author=None, expires_at=None):
    proposal = TermsProposal.objects.create(
        interest=interest,
        owner=owner,
        terms=terms,
        offer_snapshot=snapshot,
        accepted_by=[str((author or owner).id)],
        author=author,
        expires_at=expires_at,
    )
    record_consent(proposal, author or owner, "propose", {
        "selection": snapshot, "terms": terms, "content_version": proposal.content_revision,
        "expires_at": expires_at.isoformat() if expires_at else None,
    })
    if author is not None:
        from .negotiation_terms import record_version
        record_version(proposal)
    interest.status = RentalInterest.Status.PROPOSED
    interest.revision += 1
    interest.save(update_fields=["status", "revision", "updated_at"])
    return proposal


def create_invitation(*, interest, proposal, owner, snapshot):
    from .rental_phase2 import RentalConflict

    if TenancyInvitation.objects.filter(
        owner=owner,
        property=interest.property,
        tenant=interest.tenant,
        offer_id=interest.offer_id,
        status__in=["pending", "accepted"],
        lease__isnull=True,
    ).exists():
        raise RentalConflict("A live invitation already exists for this offer.")
    invitation = TenancyInvitation.objects.create(
        property=interest.property,
        owner=owner,
        tenant=interest.tenant,
        offer_id=interest.offer_id,
        offer_snapshot=snapshot,
        expires_at=timezone.now() + timedelta(days=7),
        initiated_by=owner,
        interest=interest,
        terms_proposal=proposal,
        provenance_version="independent_interest_v1",
        eligibility_snapshot={
            "interest_revision": interest.revision,
            "proposal_revision": proposal.revision,
            "offer_revision": snapshot["offer_revision"],
        },
    )
    interest.status = RentalInterest.Status.INVITED
    interest.revision += 1
    interest.save(update_fields=["status", "revision", "updated_at"])
    return invitation
