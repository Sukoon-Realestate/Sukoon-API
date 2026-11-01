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
        "required_approvals": [str(item.lease.owner.id), str(item.lease.tenant.id)],
    }
    return {**value, "digest": fingerprint(value)}
