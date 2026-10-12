"""Permissions for the template/invitation API, distinct from structured leases."""

from ..models import Lease, RentalHandover, RentalInterest, TermsProposal


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
        and user.is_active
        and user.is_verified
        and user.pk == lease.owner_id
        and lease.status == Lease.Status.DRAFT
        and not is_read_only(lease)
    )


def agreement_actions(user, lease):
    from ..providers import fake_provider_available

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
    if not fake_provider_available():
        return actions
    if lease.status == Lease.Status.DRAFT:
        if str(user.id) not in lease.reviewed_by:
            actions.append("accept_review")
        if user.pk == lease.owner_id:
            actions.append("edit_lease")
            if {str(lease.owner.id), str(lease.tenant.id)}.issubset(lease.reviewed_by):
                actions.append("submit_for_signature")
    elif lease.status == Lease.Status.PENDING_SIGNATURES and lease.document_id:
        if not lease.signing_sessions.filter(
            signer=user,
            status="completed",
            document_id=lease.document_id,
            document_hash=lease.document_hash,
        ).exists():
            actions.append("sign")
    from .cycle_permissions import cycle_actions

    return actions + cycle_actions(user, lease)


def interest_actions(user, item):
    if not user or not user.is_active or not user.is_verified:
        return []
    if item.status in {
        RentalInterest.Status.REJECTED,
        RentalInterest.Status.WITHDRAWN,
        RentalInterest.Status.INVITED,
    }:
        return []
    if user.pk == item.property.owner_id:
        actions = ["create_terms_proposal", "reject"]
        if item.terms_proposals.filter(status=TermsProposal.Status.ACCEPTED).exists():
            actions.append("create_invitation")
        return actions
    return (
        ["withdraw"]
        if user.pk == item.tenant_id and item.status == RentalInterest.Status.SUBMITTED
        else []
    )


def proposal_actions(user, item):
    if (
        not user
        or not user.is_active
        or not user.is_verified
        or user.pk not in {item.owner_id, item.interest.tenant_id}
    ):
        return []
    if item.status not in {
        TermsProposal.Status.PROPOSED,
        TermsProposal.Status.CHANGES_REQUESTED,
    }:
        return []
    actions = ["reject", "request_changes"]
    if str(user.id) not in item.accepted_by:
        actions.append("accept")
    if user.pk == item.owner_id:
        actions.append("edit_terms")
    return actions


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
