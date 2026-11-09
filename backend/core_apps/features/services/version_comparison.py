"""Comparison identity over the exact snapshots already authorized by the caller."""
from .rental_phase2 import fingerprint


def rental_change_comparison(item):
    if item.kind not in {"amendment", "renewal"}:
        return None
    base = item.previous_terms
    current = item.terms
    value = {
        "protocol": 1,
        "base_id": str(item.lease.id),
        # Historical proposals did not store the lease revision at creation.
        # The immutable snapshot digest is the binding; never invent a revision.
        "base_revision": None,
        "base_available": isinstance(base, dict) and bool(base),
        "base_digest": fingerprint(base) if base else "",
        "current_id": str(item.id),
        "current_revision": item.revision,
        "content_revision": item.content_revision,
        "current_digest": fingerprint(current),
        "document_id": str(item.document_id) if item.document_id else None,
        "document_hash": item.document_hash,
        "required_approvals": required_approvals(item.lease),
    }
    return {**value, "digest": fingerprint(value)}


def required_approvals(lease):
    """Owner plus the renter's signer: the tenant, or a company lease's current signer."""
    if lease.tenant_id:
        return [str(lease.owner.id), str(lease.tenant.id)]
    tenancy = getattr(lease, "company_tenancy", None)
    signer = tenancy.signer_mandate.membership.user if tenancy and tenancy.signer_mandate_id else None
    return [str(lease.owner.id)] + ([str(signer.id)] if signer else [])
