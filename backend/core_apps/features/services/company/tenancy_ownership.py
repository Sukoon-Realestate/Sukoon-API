"""Prospective creditor transition; old invoices, payables and deposit stay owned."""

from copy import deepcopy
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from ...models import RentalChange, DepositAgreement
from ..rental_phase2 import RentalConflict
from . import (
    tenancy_access as access,
    tenancy_changes as changes,
    tenancy_commercial as commercial,
)


def validate(item, change):
    body = change.snapshot["content"]
    candidate = get_object_or_404(
        User, id=body["new_owner_id"], is_active=True, is_verified=True
    )
    if candidate.sensitive_actions_frozen:
        raise PermissionDenied(
            "The incoming owner's account authority must be recovered first."
        )
    props = access.properties(item, lock=True)
    if not props or any(
        p.owner_id != candidate.pk or not p.is_ownership_verified for p in props
    ):
        raise RentalConflict(
            "Every included property needs independently verified current ownership by the incoming owner."
        )
    # Custody of money is never transferred by a property edit. Platform-held
    # deposits remain canonical; direct owner custody needs an approved policy.
    if item.lease.terms.get("deposit_holder") != "platform":
        raise RentalConflict(
            "An owner-held deposit requires a separately approved custody resolution."
        )
    if item.lease.invoices.filter(beneficiary__isnull=True).exists():
        raise RentalConflict(
            "Reconcile historical invoice beneficiaries before changing current ownership."
        )


def propose(item, user, data):
    access.require_role(item, user, {"owner", "signer"}, sensitive=True)
    return prepare(item, user, data)


def prepare(item, user, data):
    """Called only after participant or assigned case-operator authorization."""
    commercial.assert_no_continuation(item)
    if item.lease.status != "active":
        raise RentalConflict("Ownership continuation requires an active contract.")
    candidate = get_object_or_404(
        User, id=data["new_owner_id"], is_verified=True, is_active=True
    )
    roles = changes.current_roles(item)
    if str(candidate.id) in roles.values() or access.member(item, candidate):
        raise RentalConflict(
            "The incoming owner must be independent of company representatives."
        )
    content = {
        "new_owner_id": str(candidate.id),
        "new_owner_name": candidate.get_full_name,
        "previous_owner_id": str(item.lease.owner.id),
        "effective_rule": "after_all_exact_provider_signatures",
        "existing_invoice_beneficiaries_retained": True,
        "existing_deposit_custody_retained": True,
    }
    terms = deepcopy(item.lease.terms)
    terms.update(
        owner_id=str(candidate.id),
        previous_owner_id=str(item.lease.owner.id),
        continuation_kind="ownership",
        creditor_rule="existing_invoices_unchanged_future_issues_to_new_owner",
    )
    content["terms"] = terms
    required = {k: roles[k] for k in ["owner", "signer", "payer"]}
    required["new_owner"] = str(candidate.id)
    changes.propose(item, user, "ownership", content, required, data["reason"])
    change = item.changes.get(kind="ownership", state="pending")
    validate(item, change)
    change.rental_change = RentalChange.objects.create(
        lease=item.lease,
        requester=user,
        kind="amendment",
        terms=terms,
        previous_terms=deepcopy(item.lease.terms),
        reason=data["reason"],
    )
    change.save()
    return item


def apply(item, change):
    validate(item, change)
    body = change.snapshot["content"]
    item.lease.owner = User.objects.get(id=body["new_owner_id"])
    item.lease.terms = deepcopy(body["terms"])
    # Original signatures and documents remain on the original lease and
    # RentalChange. The new owner's private access begins only at this point.
