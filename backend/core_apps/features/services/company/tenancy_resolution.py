"""Mutual, separately signed release of an unapplied continuation.

No existing contract, invoice, deposit, possession or provider fact is reversed.
An absent party requires a separate approved adjudication policy.
"""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from ...models import CompanyTenancyChange, RentalChange
from ..rental_phase2 import RentalConflict
from . import tenancy_access as access, tenancy_changes as changes

KIND = "continuation_release"


def signing_role(role):
    return role in {"owner", "signer", "new_owner"} or role.startswith("prior_signer_")


def source(item, change):
    content = change.snapshot["content"]
    original = get_object_or_404(
        CompanyTenancyChange.objects.select_for_update(),
        tenancy=item,
        id=content["original_change_id"],
    )
    if (
        original.snapshot_digest != content["original_digest"]
        or original.state != "resolution_pending"
        or original.applied_at
        or str(original.rental_change.document_id) != content["original_document_id"]
        or original.rental_change.document_hash != content["original_document_hash"]
    ):
        raise RentalConflict(
            "The original continuation changed; reconcile its exact evidence."
        )
    return original


def propose(item, user, data):
    access.require_role(item, user, {"owner", "signer"}, sensitive=True)
    original = get_object_or_404(
        CompanyTenancyChange.objects.select_for_update(),
        tenancy=item,
        id=data["change_id"],
        kind__in=["renewal", "amendment", "ownership"],
    )
    if (
        original.snapshot_digest != data["digest"]
        or original.state not in {"accepted", "pending_signatures", "review_required"}
        or original.applied_at
    ):
        raise RentalConflict("Only an unapplied continuation can be mutually released.")
    required = {
        k: v
        for k, v in changes.current_roles(item).items()
        if k in {"owner", "signer", "payer"}
    }
    for n, identity in enumerate(
        sorted({v for k, v in original.snapshot["required"].items() if signing_role(k)})
    ):
        required[f"prior_signer_{n}"] = identity
    event = original.rental_change
    content = {
        "original_change_id": str(original.id),
        "original_digest": original.snapshot_digest,
        "original_document_id": str(event.document_id),
        "original_document_hash": event.document_hash,
        "original_kind": original.kind,
        "original_summary": {
            "kind": original.kind,
            "reason": original.reason,
            "content": {
                key: original.snapshot["content"][key]
                for key in (
                    "effective_on",
                    "ends_on_exclusive",
                    "new_owner_name",
                    "terms",
                )
                if key in original.snapshot["content"]
            },
        },
        "effect": "Release only this unapplied continuation after all named parties sign this exact resolution. Preserve the current tenancy, issued invoices, deposit custody and original signature evidence. No compensation, refund or forced discharge is established.",
    }
    changes.propose(item, user, KIND, content, required, data["reason"])
    resolution = item.changes.get(kind=KIND, state="pending")
    resolution.rental_change = RentalChange.objects.create(
        lease=item.lease,
        requester=user,
        kind="amendment",
        terms={"continuation_kind": KIND, **content, "required_parties": required},
        previous_terms={},
        reason=data["reason"],
    )
    resolution.save()
    original.state = "resolution_pending"
    original.revision += 1
    original.save()
    return item


def release_review(item, change):
    original = source(item, change)
    # Before any resolution session exists, withdrawing this proposal only
    # restores reconciliation of the original; it does not cancel its signatures.
    if change.rental_change.signing_sessions.exists():
        raise RentalConflict(
            "Reconcile the original resolution signing sessions before withdrawal."
        )
    original.state = "review_required"
    original.revision += 1
    original.save()
    change.rental_change.status = "rejected"
    change.rental_change.save()


def apply_signed(item, change):
    from .tenancy_commercial import budget

    original = source(item, change)
    if original.reserved_rent_minor:
        row = budget(item)
        if row.rent_minor < original.reserved_rent_minor:
            raise RentalConflict(
                "Reconcile the company budget before releasing the reserved increment."
            )
        row.rent_minor -= original.reserved_rent_minor
        row.save()
        original.reserved_rent_minor = 0
    original.inventory_locks.filter(kind="hold").delete()
    original.state = "resolved_unapplied"
    original.revision += 1
    original.save()
    # signed_by and all original session receipts remain unchanged, even when
    # another authoritative callback arrives after this resolution.
    original.rental_change.status = "superseded"
    original.rental_change.revision += 1
    original.rental_change.save()
    change.state, change.applied_at = "applied", timezone.now()
    change.save()
    change.rental_change.status, change.rental_change.applied_at = (
        "applied",
        timezone.now(),
    )
    change.rental_change.revision += 1
    change.rental_change.save()
