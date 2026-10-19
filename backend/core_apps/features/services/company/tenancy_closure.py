"""Use existing termination and funded-settlement rules for a company debtor."""

from datetime import date
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from ...models import (
    CompanyMandate,
    CompanyMembership,
    FinalSettlement,
    RentalChange,
    CompanyBudgetReservation,
)
from ..rental_phase2 import RentalConflict, fingerprint
from ..rental_phase6 import evaluate_financial_closure
from ..settlements import (
    prepare_settlement,
    financial_snapshot,
    execute_settlement,
    LINE_TYPES,
)
from . import tenancy_access as access, tenancy_changes as changes


def propose_termination(item, user, data):
    access.require_role(item, user, {"owner", "signer"}, sensitive=True)
    if user.pk != item.lease.owner_id:
        access.require_delegate(item, user, "sign")
    if item.lease.status not in {"signed", "active"}:
        raise RentalConflict(
            "Only a signed or active company tenancy can enter bilateral termination."
        )
    day = data["effective_on"]
    if (
        not max(timezone.localdate(), item.lease.start_date)
        <= day
        <= item.lease.end_date
    ):
        raise RentalConflict("Choose a current or future end within this tenancy.")
    # No new proration rule. Restrict the effective boundary to an existing billing boundary.
    boundaries = set(item.lease.billing_periods.values_list("start", flat=True)) | {
        item.lease.end_date
    }
    if day not in boundaries:
        raise RentalConflict(
            "Choose an existing billing boundary; partial-period pricing is not approved.",
            code="partial_period_unsupported",
        )
    roles = changes.current_roles(item)
    return changes.propose(
        item,
        user,
        "termination",
        {
            "effective_on": str(day),
            "previous_end": str(item.lease.end_date),
            "previous_status": item.lease.status,
        },
        {k: roles[k] for k in ["owner", "signer", "payer"]},
        data["reason"],
    )


def apply_termination(item, change):
    content = change.snapshot["content"]
    if (
        item.lease.status != content["previous_status"]
        or str(item.lease.end_date) != content["previous_end"]
    ):
        raise RentalConflict("The company tenancy changed before termination approval.")
    event = RentalChange.objects.create(
        lease=item.lease,
        requester=change.proposed_by,
        kind="termination",
        status="applied",
        reason=change.reason,
        effective_on=date.fromisoformat(content["effective_on"]),
        approvals=list(change.snapshot["required"].values()),
        applied_at=timezone.now(),
    )
    from ..legal_lifecycle import accept_termination

    accept_termination(event)
    event.save()


def settlement_lines(lease, raw):
    from ..commands import money_minor
    import uuid

    rows, seen = [], set()
    if not isinstance(raw, list) or len(raw) > 100:
        raise ValidationError("Supply at most 100 settlement lines.")
    for line in raw:
        if not isinstance(line, dict) or line.get("type") not in LINE_TYPES:
            raise ValidationError("Choose a supported settlement line type.")
        identity = str(line.get("id") or uuid.uuid4())
        if identity in seen:
            raise ValidationError("Each settlement line needs a distinct identity.")
        seen.add(identity)
        amount = money_minor(line.get("amount"), allow_negative=True)
        description = str(line.get("description", "")).strip()
        if len(description) > 2000:
            raise ValidationError(
                "Settlement descriptions are limited to 2000 characters."
            )
        from ...rental_phase4_views_parts.handover_payload import _validate_evidence

        evidence_ids = line.get("evidence_ids", [])
        if not isinstance(evidence_ids, list) or len(evidence_ids) > 5:
            raise ValidationError(
                "Each settlement line supports at most five evidence files."
            )
        try:
            evidence_ids = [str(uuid.UUID(str(value))) for value in evidence_ids]
        except (ValueError, TypeError, AttributeError):
            raise ValidationError("Evidence references must be valid identifiers.")
        evidence = _validate_evidence(lease, evidence_ids)
        rows.append(
            {
                "id": identity,
                "type": line["type"],
                "description": description,
                "amount": {"amount_minor": amount, "currency": "EGP", "exponent": 2},
                "evidence_ids": [str(e.id) for e in evidence],
                **(
                    {"invoice_id": str(line["invoice_id"])}
                    if line.get("invoice_id")
                    else {}
                ),
            }
        )
    return rows


def propose_settlement(item, user, data):
    access.require_role(item, user, {"owner", "payer"}, sensitive=True)
    if user.pk != item.lease.owner_id:
        access.require_delegate(item, user, "pay")
    rows = settlement_lines(item.lease, data["lines"])
    plan = prepare_settlement(item.lease, rows)
    existing = FinalSettlement.objects.filter(lease=item.lease).first()
    if existing and existing.execution_status == "executed":
        raise RentalConflict(
            "An executed settlement needs an authorized adjustment, not replacement."
        )
    roles = changes.current_roles(item)
    return changes.propose(
        item,
        user,
        "settlement",
        {
            "lines": rows,
            "plan": plan,
            "financial_snapshot": financial_snapshot(item.lease),
        },
        {k: roles[k] for k in ["owner", "signer", "payer"]},
        data["reason"],
    )


def apply_settlement(item, change):
    body = change.snapshot["content"]
    from ...rental_phase4_views_parts.handover_payload import _validate_evidence

    for line in body["lines"]:
        _validate_evidence(item.lease, line.get("evidence_ids", []))
    if fingerprint(financial_snapshot(item.lease)) != fingerprint(
        body["financial_snapshot"]
    ):
        raise RentalConflict(
            "Financial records changed; review a fresh settlement.",
            code="settlement_financial_state_changed",
        )
    plan = prepare_settlement(item.lease, body["lines"])
    if plan != body["plan"]:
        raise RentalConflict("The agreed financial allocation changed.")
    settlement, _ = FinalSettlement.objects.get_or_create(lease=item.lease)
    if settlement.execution_status == "executed":
        raise RentalConflict("This settlement has already been executed.")
    settlement.lines = body["lines"]
    settlement.financial_snapshot = body["financial_snapshot"]
    settlement.execution_plan = plan
    settlement.status = "accepted"
    settlement.accepted_by = list(change.snapshot["required"].values())
    settlement.proposed_by = change.proposed_by
    for key in [
        "rent_balance_minor",
        "deposit_to_return_minor",
        "refund_due_minor",
        "total_due_minor",
    ]:
        setattr(settlement, key, plan[key])
    settlement.revision += 1
    settlement.save()
    execute_settlement(settlement)
    from ...models import RentalDocument

    RentalDocument.objects.get_or_create(
        lease=item.lease,
        document_type="settlement",
        defaults={
            "requested_by": change.proposed_by,
            "title": "Company final settlement",
        },
    )
    evaluate_financial_closure(item.lease, increment_revision=False)


def close_budget(item):
    """Synchronize the company projection under the canonical company/lease locks.

    Reopening preserves the original approved exposure, never creates a charge or
    allocates inventory again. Closure cannot leave that exposure falsely free.
    """
    booking = item.preparation.booking
    if item.lease.financial_closure_status == "closed":
        status, budget_status = "closed", "released"
    elif booking.status in {"closed", "financial_review"}:
        status, budget_status = "financial_review", "committed"
    else:
        return
    CompanyBudgetReservation.objects.filter(item=booking).update(status=budget_status)
    if booking.status != status:
        booking.status = status
        booking.revision += 1
        booking.save(update_fields=["status", "revision", "updated_at"])


def reconcile(item, user, data):
    access.require_role(item, user, {"owner", "coordinator", "signer", "payer"})
    from .tenancy_initial_recovery import reconcile as reconcile_initial

    reconcile_initial(item)
    from .tenancy_expiry import expire

    expire(item)
    item.lease.refresh_from_db()
    from ..legal_lifecycle import end_lease_if_due

    end_lease_if_due(item.lease)
    evaluate_financial_closure(item.lease, increment_revision=False)
    return access.changed(item, user, "company_tenancy_reconciled")


def propose_authority(item, user, data):
    access.require_role(item, user, {"administrator"}, sensitive=True)
    # Replace an absent delegate using new independently verified authority;
    # the former delegate cannot veto the company's legitimate succession.
    signer = get_object_or_404(
        CompanyMandate,
        id=data["signer_mandate_id"],
        company=item.lease.renter_company,
        kind="sign",
    )
    payer = get_object_or_404(
        CompanyMandate,
        id=data["payer_mandate_id"],
        company=item.lease.renter_company,
        kind="pay",
    )
    from .tenancy_commercial import exposure as current_exposure

    exposure = current_exposure(item)
    if item.lease.owner_id in {signer.membership.user_id, payer.membership.user_id}:
        raise PermissionDenied(
            "The owner cannot represent the renting company in this tenancy."
        )
    if not all(access.execution_mandate(m, exposure=exposure) for m in [signer, payer]):
        raise RentalConflict(
            "Both replacement mandates need current independent execution verification."
        )
    reviewer = get_object_or_404(
        CompanyMembership,
        company=item.lease.renter_company,
        id=data["reviewer_membership_id"],
        is_active=True,
        is_admin=True,
    )
    coordinator = get_object_or_404(
        CompanyMembership,
        company=item.lease.renter_company,
        id=data["coordinator_membership_id"],
        is_active=True,
        is_coordinator=True,
        user__is_active=True,
        user__is_verified=True,
        user__sensitive_actions_frozen=False,
    )
    if coordinator.user_id == item.lease.owner_id:
        raise PermissionDenied(
            "Company possession requires a coordinator distinct from the owner."
        )
    if reviewer.user_id in {
        user.pk,
        signer.membership.user_id,
        payer.membership.user_id,
        coordinator.user_id,
        item.lease.owner_id,
    }:
        raise PermissionDenied("Choose an independent active company administrator.")
    if item.lease.status not in {
        "signed",
        "active",
        "termination_pending",
        "ended",
        "cancelled",
    }:
        raise RentalConflict(
            "Review a new unsigned draft instead of replacing its contract parties."
        )
    required = {
        "administrator": str(reviewer.user.id),
        "new_signer": str(signer.membership.user.id),
        "new_payer": str(payer.membership.user.id),
        "new_coordinator": str(coordinator.user.id),
    }
    return changes.propose(
        item,
        user,
        "authority",
        {
            "signer_mandate_id": str(signer.id),
            "payer_mandate_id": str(payer.id),
            "signer_revision": signer.revision,
            "payer_revision": payer.revision,
            "signer_name": signer.membership.user.get_full_name,
            "payer_name": payer.membership.user.get_full_name,
            "reviewer_name": reviewer.user.get_full_name,
            "coordinator_name": coordinator.user.get_full_name,
            "coordinator_membership_id": str(coordinator.id),
            "coordinator_revision": coordinator.revision,
            "previous_coordinator_id": str(item.coordinator.id),
            "previous_signer": str(item.signer_mandate.id),
            "previous_payer": str(item.payer_mandate.id),
        },
        required,
        data["reason"],
    )


def apply_authority(item, change):
    from .tenancy_commercial import exposure as current_exposure

    body = change.snapshot["content"]
    if (
        str(item.signer_mandate.id) != body["previous_signer"]
        or str(item.payer_mandate.id) != body["previous_payer"]
        or str(item.coordinator.id) != body["previous_coordinator_id"]
    ):
        raise RentalConflict("The company delegates changed during review.")
    next_mandates = [
        get_object_or_404(
            CompanyMandate,
            id=body[k + "_mandate_id"],
            revision=body[k + "_revision"],
            company=item.lease.renter_company,
        )
        for k in ["signer", "payer"]
    ]
    if not all(
        access.execution_mandate(
            m,
            exposure=current_exposure(item),
        )
        for m in next_mandates
    ):
        raise RentalConflict("Replacement authority is no longer current.")
    if any(m.membership.user_id == item.lease.owner_id for m in next_mandates):
        raise PermissionDenied(
            "The owner cannot represent the renting company in this tenancy."
        )
    item.signer_mandate, item.payer_mandate = next_mandates
    coordinator = get_object_or_404(
        CompanyMembership,
        id=body["coordinator_membership_id"],
        company=item.lease.renter_company,
        revision=body["coordinator_revision"],
        is_active=True,
        is_coordinator=True,
    )
    if coordinator.user_id == item.lease.owner_id:
        raise PermissionDenied(
            "Company possession requires a coordinator distinct from the owner."
        )
    item.coordinator = coordinator.user
    item.save(
        update_fields=["signer_mandate", "payer_mandate", "coordinator", "updated_at"]
    )
    # This changes current representation, never the historical signatory or debtor.
