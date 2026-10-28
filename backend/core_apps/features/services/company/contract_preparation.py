"""Ordinary company review cycle through the explicitly unavailable provider boundary."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from ...company_models import CompanyBookingItem
from ...company_contract_models import (
    CompanyMandate,
    CompanyContractPreparation,
    CompanyPreparationConsent,
)
from core_apps.users.models import User
from ..rental_lifecycle.common import audit, require_revision
from ..rental_phase2 import RentalConflict, fingerprint
from .access import request_for, require_new_business
from . import contract_access as access, contract_snapshot as snapshots


def account_parties(booking_id, data):
    from .access import booking_account_parties

    parties = booking_account_parties(booking_id, include_preparation=False)
    parties.update(
        CompanyMandate.objects.filter(
            id__in=[data["signer_mandate_id"], data["payer_mandate_id"]]
        ).values_list("membership__user_id", flat=True)
    )
    return parties


def existing_account_parties(identity):
    item = get_object_or_404(CompanyContractPreparation, id=identity)
    return account_parties(
        item.booking.id,
        {
            "signer_mandate_id": item.signer_mandate.id,
            "payer_mandate_id": item.payer_mandate.id,
        },
    )


def booking_for(user, identity, *, lock=False):
    initial = get_object_or_404(CompanyBookingItem, id=identity)
    request_for(user, initial.request.id, lock=lock)
    query = (
        CompanyBookingItem.objects.select_for_update()
        if lock
        else CompanyBookingItem.objects
    )
    return query.get(pk=initial.pk)


def notify(item, *, coordinator_only=False):
    from .role_notifications import record

    required = [] if coordinator_only else list(snapshots.required(item.snapshot))
    required.append((str(item.booking.request.coordinator.id), "coordinator"))
    for actor, role in set(required):
        record(
            user=User.objects.get(id=actor),
            company=item.booking.request.company,
            role=role,
            key=f"company.contract:{item.id}:{item.revision}",
            destination={
                "action_type": "open_company_contract",
                "target_id": str(item.id),
                "schema_version": "1",
                "workspace": "owner" if role == "owner" else "company",
            },
        )


@transaction.atomic
def prepare(user, booking_id, data):
    require_new_business()
    from .access import lock_account_parties

    lock_account_parties(user, account_parties(booking_id, data))
    booking = booking_for(user, booking_id, lock=True)
    existing = (
        CompanyContractPreparation.objects.select_for_update()
        .filter(booking=booking)
        .first()
    )
    require_revision(existing or booking, data["expected_revision"])
    if existing and existing.state == "withdrawn":
        raise RentalConflict(
            "This preparation was withdrawn. Start a new package.",
            code="preparation_closed",
        )
    cycle = existing.snapshot["cycle"] + 1 if existing else 1
    snapshot = snapshots.source(
        booking,
        data["signer_mandate_id"],
        data["payer_mandate_id"],
        data["placements"],
        cycle=cycle,
        lock=True,
    )
    from ..advanced_execution.progress import validate_company_preparation

    validate_company_preparation(booking, snapshot)
    item = existing or CompanyContractPreparation(booking=booking, created_by=user)
    item.signer_mandate = CompanyMandate.objects.get(id=data["signer_mandate_id"])
    item.payer_mandate = CompanyMandate.objects.get(id=data["payer_mandate_id"])
    item.snapshot, item.snapshot_digest = snapshot, fingerprint(snapshot)
    item.state = "awaiting_reviews"
    if existing:
        item.revision += 1
    item.save()
    for actor, role in snapshots.required(snapshot):
        CompanyPreparationConsent.objects.create(
            preparation=item,
            actor=User.objects.get(id=actor),
            role=role,
            snapshot_digest=item.snapshot_digest,
            decision="pending",
        )
    audit(
        item,
        user,
        "company_contract_prepared",
        metadata={
            "snapshot_digest": item.snapshot_digest,
            "cycle": cycle,
            "snapshot": snapshot,
        },
    )
    notify(item)
    return item


@transaction.atomic
def respond(user, identity, data):
    from .access import lock_account_parties

    lock_account_parties(user, existing_account_parties(identity))
    item = access.get(user, identity, lock=True)
    require_revision(item, data["expected_revision"])
    if (
        item.state not in {"awaiting_reviews", "changes_requested", "reviews_complete"}
        or item.booking.status == "withdrawn"
        or data["snapshot_digest"] != item.snapshot_digest
    ):
        raise RentalConflict(
            "Review the current company preparation before responding.",
            code="preparation_changed",
        )
    if data["role"] not in access.roles_for(item, user):
        raise PermissionDenied("Respond only for your own assigned responsibility.")
    row = get_object_or_404(
        CompanyPreparationConsent,
        preparation=item,
        actor=user,
        role=data["role"],
        snapshot_digest=item.snapshot_digest,
    )
    decision = data["decision"]
    if not (
        (row.decision == "pending" and decision in {"accepted", "declined"})
        or (row.decision == "accepted" and decision == "withdrawn")
    ):
        raise RentalConflict(
            "This review is already recorded. A changed plan requires fresh review.",
            code="review_recorded",
        )
    if decision == "accepted":
        require_new_business()
        snapshots.revalidate(item, lock=True)
    row.decision, row.reason, row.revision = decision, data["reason"], row.revision + 1
    row.save()
    states = list(
        item.consents.filter(snapshot_digest=item.snapshot_digest).values_list(
            "decision", flat=True
        )
    )
    item.state = (
        "changes_requested"
        if any(s in {"declined", "withdrawn"} for s in states)
        else (
            "reviews_complete"
            if states and all(s == "accepted" for s in states)
            else "awaiting_reviews"
        )
    )
    item.revision += 1
    item.save()
    audit(
        item,
        user,
        "company_contract_review_" + decision,
        data["reason"],
        metadata={"role": row.role, "snapshot_digest": item.snapshot_digest},
    )
    notify(item, coordinator_only=True)
    return item


@transaction.atomic
def withdraw(user, identity, data):
    item = access.get(user, identity, lock=True)
    if not access.manages(item, user):
        raise PermissionDenied(
            "Only the currently assigned coordinator can withdraw this package."
        )
    require_revision(item, data["expected_revision"])
    if item.state == "withdrawn":
        raise RentalConflict(
            "This preparation is already withdrawn.", code="preparation_closed"
        )
    from .bookings import withdraw_item

    withdraw_item(user, item.booking.id, {"expected_revision": item.booking.revision})
    item.refresh_from_db()
    return item


def cancel_for_booking(booking, user):
    item = (
        CompanyContractPreparation.objects.select_for_update()
        .filter(booking=booking)
        .first()
    )
    if item and item.state != "withdrawn":
        item.state = "withdrawn"
        item.revision += 1
        item.save()
        audit(item, user, "company_contract_withdrawn")
        notify(item)


def require_reviews_for_booking(booking):
    item = (
        CompanyContractPreparation.objects.select_for_update()
        .filter(booking=booking)
        .first()
    )
    if item:
        if item.state != "reviews_complete":
            raise RentalConflict(
                "Every assigned participant must confirm the current plan before this reservation.",
                code="reviews_required",
            )
        snapshots.revalidate(item, lock=True)


def hold_recorded(booking, user):
    item = (
        CompanyContractPreparation.objects.select_for_update()
        .filter(booking=booking)
        .first()
    )
    if item:
        item.revision += 1
        item.save()
        audit(item, user, "company_contract_inventory_reserved")
        notify(item)


@transaction.atomic
def reserve(user, identity, data):
    from .access import lock_account_parties

    lock_account_parties(user, existing_account_parties(identity))
    item = access.get(user, identity, lock=True)
    if not access.manages(item, user):
        raise PermissionDenied(
            "Only the currently assigned coordinator can reserve this package."
        )
    require_revision(item, data["expected_revision"])
    if item.state != "reviews_complete":
        raise RentalConflict(
            "Every assigned participant must confirm the current plan before this reservation.",
            code="reviews_required",
        )
    snapshots.revalidate(item, lock=True)
    from .bookings import hold_item

    hold_item(user, item.booking.id, {"expected_revision": item.booking.revision})
    item.refresh_from_db()
    return item
