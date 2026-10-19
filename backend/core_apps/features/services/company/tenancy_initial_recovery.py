"""Exact, separately signed release before initial company financial execution.

Current policy publication authorizes proposing a new resolution; it never
rewrites the original agreement or treats review/nonresponse as a signature.
"""

from django.utils import timezone
from ...models import (
    CompanyBudgetReservation,
    Company,
    CompanyMandate,
    DepositAgreement,
    PaymentAttempt,
    RentalChange,
    ReservationHold,
)
from ..business_policies import current, snapshot
from ..rental_phase2 import RentalConflict
from . import tenancy_access as access, tenancy_changes as changes

KIND = "agreement_release"
SCOPE = "company.agreement.release"
OPEN = {"pending", "accepted", "pending_signatures", "review_required"}


def policy():
    result = current("D02")
    return (
        result
        if result
        and SCOPE in result.scope
        and result.rules.get("resolution_mode") == "mutual_signed_release"
        else None
    )


def sessions(item):
    # Provider results may arrive later. Their immutable identities belong in
    # the release; changing completion status must never erase or replace them.
    return [
        {
            "id": str(row.id),
            "provider_session_id": row.provider_session_id,
            "signer_id": str(row.signer.id),
            "document_id": str(row.document_id),
            "document_hash": row.document_hash,
        }
        for row in item.lease.signing_sessions.select_related("signer").order_by("id")
    ]


def authority(item):
    company = Company.objects.get(pk=item.lease.renter_company_id)
    result = {
        "company_id": str(company.id),
        "company_revision": company.revision,
        "company_review_status": company.review_status,
        "owner_id": str(item.lease.owner.id),
        "property_owners": [
            {"id": str(prop.id), "owner_id": str(prop.owner.id)}
            for prop in access.properties(item)
        ],
    }
    for role, identity in [
        ("signer", item.signer_mandate_id),
        ("payer", item.payer_mandate_id),
    ]:
        mandate = CompanyMandate.objects.select_related("membership").get(pk=identity)
        result[role] = {
            "id": str(mandate.id),
            "revision": mandate.revision,
            "membership_id": str(mandate.membership.id),
            "membership_revision": mandate.membership.revision,
        }
    return result


def boundary_error(item):
    lease = item.lease
    if (
        lease.status != "pending_signatures"
        or not lease.document_id
        or not lease.document_hash
    ):
        return "Only an initial agreement awaiting signatures can use this pre-financial release."
    if (
        lease.occupancy_status != "not_started"
        or lease.handovers.exists()
        or item.preparation.booking.assignments.exclude(
            occupancy_status__in=["arrival_pending", "cancelled"]
        ).exists()
    ):
        return (
            "Actual possession must use the tenancy departure and settlement process."
        )
    if (
        lease.invoices.exists()
        or lease.billing_periods.exists()
        or lease.ledger_transactions.exists()
        or lease.owner_payables.exists()
        or lease.refund_requests.exists()
        or lease.payouts.exists()
        or PaymentAttempt.objects.filter(invoice__lease=lease).exists()
        or DepositAgreement.objects.filter(lease=lease).exists()
    ):
        return "An invoice, payment instruction or financial effect requires canonical financial resolution."
    if lease.renter_company.review_status != "verified" or any(
        prop.owner_id != lease.owner_id for prop in access.properties(item)
    ):
        return "Verify the company's current authority and the original property owner's responsibility first."
    identities = sessions(item)
    if not identities or any(
        not row["provider_session_id"]
        or row["document_id"] != str(lease.document_id)
        or row["document_hash"] != lease.document_hash
        for row in identities
    ):
        return "Reconcile the exact original provider session and document identities first."
    if {row["signer_id"] for row in identities} - {
        str(lease.owner.id),
        str(item.signer_mandate.membership.user.id),
    }:
        return "The original signatory responsibility changed; independent authority resolution is required."
    return None


def pending(item):
    return item.changes.filter(kind=KIND, state__in=OPEN).exists()


def can_propose(item):
    return bool(policy() and not boundary_error(item) and not pending(item))


def matches(item, change):
    content, lease = change.snapshot["content"], item.lease
    return (
        content.get("original_document_id") == str(lease.document_id)
        and content.get("original_document_hash") == lease.document_hash
        and content.get("original_terms_digest") == item.terms_digest
        and content.get("original_sessions") == sessions(item)
    )


def applied(item):
    if item.lease.status != "cancelled":
        return False
    return any(
        change.rental_change_id
        and change.rental_change.status == "applied"
        and change.rental_change.applied_at
        and change.rental_change.document_id
        and change.rental_change.document_hash
        and {
            identity
            for role, identity in change.snapshot["required"].items()
            if role in {"owner", "signer"}
        }.issubset(change.rental_change.signed_by)
        and matches(item, change)
        for change in item.changes.filter(kind=KIND, state="applied").select_related(
            "rental_change"
        )
    )


def propose(item, user, data):
    access.require_role(item, user, {"owner", "signer"}, sensitive=True)
    if user.pk != item.lease.owner_id:
        access.require_delegate(item, user, "sign")
    selected = policy()
    if not selected:
        raise RentalConflict(
            "Publish an approved initial-agreement release policy before proposing this separate resolution.",
            code="initial_release_policy_required",
        )
    error = boundary_error(item)
    if error:
        raise RentalConflict(error)
    if data["digest"] != item.lease.document_hash:
        raise RentalConflict("Review the exact original agreement document.")
    required = {
        role: identity
        for role, identity in changes.current_roles(item).items()
        if role in {"owner", "signer", "payer"}
    }
    content = {
        "original_document_id": str(item.lease.document_id),
        "original_document_hash": item.lease.document_hash,
        "original_terms_digest": item.terms_digest,
        "original_sessions": sessions(item),
        "release_authority": authority(item),
        "policy": snapshot(selected),
        "policy_scope": SCOPE,
        "effect": (
            'Mutually release this exact initial company agreement before possession or any '
            'financial execution. Preserve original signature evidence, including late results. '
            'No fee, refund, compensation or forgiveness is created.'
        ),
    }
    changes.propose(item, user, KIND, content, required, data["reason"])
    change = item.changes.get(kind=KIND, state="pending")
    change.rental_change = RentalChange.objects.create(
        lease=item.lease,
        requester=user,
        kind="amendment",
        terms={"continuation_kind": KIND, **content, "required_parties": required},
        previous_terms={},
        reason=data["reason"],
    )
    change.save()
    return item


def revalidate(item, change):
    error = boundary_error(item)
    if error or not matches(item, change):
        raise RentalConflict(
            error
            or "The original agreement or provider identities changed; review a fresh resolution."
        )
    if change.snapshot["content"].get("release_authority") != authority(item):
        raise RentalConflict(
            "Company, mandate or membership authority changed; obtain a fresh release review."
        )
    accepted = change.snapshot["content"].get("policy", {})
    if (
        accepted.get("code") != "D02"
        or change.snapshot["content"].get("policy_scope") != SCOPE
        or accepted.get("rules", {}).get("resolution_mode") != "mutual_signed_release"
    ):
        raise RentalConflict(
            "The resolution has no accepted mutual-release policy snapshot."
        )


def withdraw(item, change):
    if change.rental_change.signing_sessions.exists():
        raise RentalConflict(
            "Reconcile the original resolution signing sessions before withdrawal."
        )
    change.rental_change.status = "rejected"
    change.rental_change.revision += 1
    change.rental_change.save()


def apply_signed(item, change):
    # The outer canonical company/property/lease locks serialize this check with
    # original callbacks, checkout and every competing company command.
    revalidate(item, change)
    lease = item.lease
    lease.inventory_day_locks.filter(kind="hold").delete()
    ReservationHold.objects.filter(lease=lease).update(
        status="released", released_at=timezone.now()
    )
    CompanyBudgetReservation.objects.filter(
        item=item.preparation.booking, status="reserved"
    ).update(status="released")
    item.preparation.booking.assignments.update(occupancy_status="cancelled")
    booking = item.preparation.booking
    booking.status = "cancelled"
    booking.revision += 1
    booking.save()
    lease.status = "cancelled"
    from ..rental_phase6 import evaluate_financial_closure

    evaluate_financial_closure(lease, increment_revision=False)
    # Keep lease.document_id/hash and every SigningSession untouched. The new
    # signed release has its own RentalChange document and provider sessions.
    change.state, change.applied_at = "applied", timezone.now()
    change.save()
    change.rental_change.status = "applied"
    change.rental_change.applied_at = timezone.now()
    change.rental_change.revision += 1
    change.rental_change.save()


def reconcile(item):
    if item.lease.status != "pending_signatures" or pending(item):
        return
    from .tenancy_contracts import complete_signature

    for session in item.lease.signing_sessions.filter(
        status="review_required", completed_at__isnull=False
    ):
        complete_signature(session, reconcile=True)
    item.lease.refresh_from_db()
