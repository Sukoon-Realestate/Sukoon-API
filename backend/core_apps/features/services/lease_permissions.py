"""Permissions for the template/invitation API, distinct from structured leases."""

from django.utils import timezone

from ..models import (
    Lease,
    RentalHandover,
    RentalInterest,
    TenancyInvitation,
    TermsProposal,
)


def supports_invitation_draft(lease):
    # Keep the persisted legacy flag: structured workflows and the legacy
    # allocation uniqueness constraint still depend on it. Only linked,
    # invitation-backed drafts have the narrow cancellation exception.
    return bool(
        lease.legacy_read_only
        and not lease.terms
        and lease.status == Lease.Status.DRAFT
        and getattr(lease, "tenancy_invitation", None) is not None
    )


def is_read_only(lease):
    return lease.legacy_read_only and not supports_invitation_draft(lease)


def can_cancel_draft(user, lease):
    return bool(
        user
        and not lease.renter_company_id
        and user.is_active
        and user.is_verified
        and user.pk == lease.owner_id
        and lease.status == Lease.Status.DRAFT
        and not is_read_only(lease)
    )


def can_revoke_invitation(user, invitation):
    return bool(
        user
        and user.is_active
        and user.is_verified
        and user.pk == invitation.owner_id
        and not invitation.lease_id
        and not invitation.consumed_at
        and invitation.status
        in {TenancyInvitation.Status.PENDING, TenancyInvitation.Status.ACCEPTED}
        and invitation.expires_at > timezone.now()
    )


def agreement_actions(user, lease):
    from ..providers import signing_available

    if lease.renter_company_id:
        return []  # Company responsibilities use the company tenancy projection.

    if (
        not user
        or not user.is_active
        or not user.is_verified
        or user.pk not in {lease.owner_id, lease.tenant_id}
    ):
        return []
    if lease.legacy_read_only:
        return ["cancel_draft"] if can_cancel_draft(user, lease) else []
    actions = ["cancel_draft"] if can_cancel_draft(user, lease) else []
    if lease.status == Lease.Status.DRAFT:
        if str(user.id) not in lease.reviewed_by:
            actions.append("accept_review")
        if user.pk == lease.owner_id:
            actions.append("edit_lease")
            if signing_available() and {
                str(lease.owner.id),
                str(lease.tenant.id),
            }.issubset(lease.reviewed_by):
                actions.append("submit_for_signature")
    elif (
        signing_available()
        and lease.status == Lease.Status.PENDING_SIGNATURES
        and lease.document_id
    ):
        if not lease.signing_sessions.filter(
            signer=user,
            status="completed",
            document_id=lease.document_id,
            document_hash=lease.document_hash,
        ).exists():
            actions.append("sign")
    from .cycle_permissions import cycle_actions

    return actions + cycle_actions(user, lease)


def interest_creation_blocker(user, property_obj):
    if not user or not user.is_active or not user.is_verified:
        return "A verified active account is required."
    if user.pk == property_obj.owner_id:
        return "An owner cannot submit interest in their own property."
    if (
        not property_obj.is_verified
        or property_obj.status != property_obj.Status.VERIFIED
    ):
        return "Rental interest requires a verified, available property."
    return None


def interest_actions(user, item):
    from .shared_housing.access import individual_actions

    if not individual_actions(item):
        return []
    from .negotiation_terms import active_negotiation

    if not user or not user.is_active or not user.is_verified:
        return []
    if item.status in {
        RentalInterest.Status.REJECTED,
        RentalInterest.Status.WITHDRAWN,
        RentalInterest.Status.INVITED,
    }:
        return []
    if user.pk == item.property.owner_id:
        actions = ["reject", "request_information", "mark_under_review"]
        if not active_negotiation(item):
            actions.insert(0, "create_terms_proposal")
        if item.terms_proposals.filter(
            status=TermsProposal.Status.ACCEPTED, expires_at__gt=timezone.now()
        ).exists():
            actions.append("create_invitation")
        return actions
    if user.pk == item.tenant_id:
        actions = ["withdraw"]
        if not active_negotiation(item):
            actions.append("create_terms_proposal")
        if item.waiting_for == "tenant":
            actions.append("provide_information")
        return actions
    return []


def proposal_actions(user, item):
    from .shared_housing.access import individual_actions

    if not individual_actions(item.interest):
        return []
    from .negotiation_terms import actions

    return actions(user, item)


def handover_actions(user, item):
    if (
        not user
        or not user.is_active
        or not user.is_verified
        or user.pk not in {item.lease.owner_id, item.lease.tenant_id}
    ):
        return []
    if item.status == RentalHandover.Status.ACCEPTED or item.lease.legacy_read_only:
        return []
    actions = ["edit_handover", "dispute"]
    if str(user.id) not in item.approvals:
        actions.append("accept")
    return actions
