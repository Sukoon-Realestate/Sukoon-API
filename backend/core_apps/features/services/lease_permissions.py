"""Permissions for the template/invitation API, distinct from structured leases."""

from ..models import Lease


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
