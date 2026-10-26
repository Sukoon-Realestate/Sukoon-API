"""Read canonical outcomes without submitting signatures or payments."""

from ...models import CompanyBookingItem, RentalProviderInstruction, PaymentAttempt
from ..rental_lifecycle.inventory import unresolved_payment
from .registry import adapter


def canonical_lease(leg):
    if leg.lease_id:
        return leg.lease
    if leg.canonical_kind == "company":
        booking = (
            CompanyBookingItem.objects.select_related("lease")
            .filter(id=leg.canonical_id)
            .first()
        )
        return booking.lease if booking else None
    return None


def outcome(leg, lease):
    if not lease:
        if leg.canonical_kind == "company":
            from django.utils import timezone

            booking = CompanyBookingItem.objects.select_related("hold").get(
                id=leg.canonical_id
            )
            if booking.status in {"withdrawn", "cancelled"}:
                return "withdrawn", False
            if booking.hold_id and (
                booking.hold.status in {"expired", "released"}
                or booking.hold.expires_at <= timezone.now()
            ):
                return "expired", False
        return leg.state, False
    payments = PaymentAttempt.objects.filter(
        invoice__lease=lease, invoice__billing_period__sequence=1
    )
    unknown = payments.filter(
        payment_status__in=["created", "pending", "authorized"]
    ).exists()
    activation_review = payments.filter(
        payment_status="captured", failure_code="activation_review_required"
    ).exists()
    document = lease.signing_documents.filter(id=lease.document_id).first()
    unknown |= bool(
        lease.status in {"draft", "pending_signatures"}
        and document
        and document.status in {"requesting", "unknown"}
    )
    if lease.status in {"active", "termination_pending", "ended"}:
        state = "confirmed"
    elif lease.status in {"cancelled", "expired"}:
        state = "withdrawn" if lease.status == "cancelled" else "expired"
    elif activation_review or (document and document.status == "review_required"):
        state = "manual_resolution"
    elif lease.status == "signed":
        latest = payments.order_by("-created_at", "-pk").first()
        state = (
            "payment_failed"
            if latest and latest.payment_status in {"failed", "cancelled", "expired"}
            else "signed"
        )
    elif lease.status == "pending_signatures":
        state = "signing" if document and document.provider_document_id else "held"
    else:
        state = "held"
    return state, unknown


def refresh(plan, *, persist=False):
    previous_plan_state = plan.state
    changed_leg = False
    legs = list(plan.legs.select_related("lease"))
    unknown = False
    for leg in legs:
        previous = leg.state
        lease = canonical_lease(leg)
        if lease:
            leg.lease = lease
        leg.state, pending = outcome(leg, lease)
        unknown |= pending
        if persist:
            leg.save(update_fields=["lease", "state", "updated_at"])
            if previous != leg.state:
                changed_leg = True
                from .plans import record_step

                record_step(
                    plan,
                    leg,
                    "canonical_progress",
                    leg.state,
                    "lease" if lease else "company_booking",
                    lease.id if lease else leg.canonical_id,
                    {"provider_mode": "test"},
                )
    states = [leg.state for leg in legs]
    if unknown:
        plan.state = "unknown"
    elif plan.case_id and plan.case.status not in {"resolved", "closed"}:
        plan.state = "manual_resolution"
    elif plan.state == "closed_partial":
        pass
    elif states and all(state == "confirmed" for state in states):
        plan.state = "completed"
    elif "payment_failed" in states:
        plan.state = "partial" if "confirmed" in states else "executing"
    elif any(
        state in {"withdrawn", "expired", "failed", "manual_resolution"}
        for state in states
    ):
        plan.state = "partial" if "confirmed" in states else "manual_resolution"
    elif plan.state not in {"awaiting_consents", "ready"}:
        plan.state = (
            "executing"
            if any(state in {"signing", "signed", "confirmed"} for state in states)
            else "prepared"
        )
    completion = getattr(adapter(plan.source_kind), "completion_state", None)
    if completion:
        plan.state = completion(plan, plan.state)
    if persist and not changed_leg and previous_plan_state != plan.state:
        from .plans import record_step

        record_step(plan, None, "canonical_progress_summary", plan.state)
    return legs


def reconcile_progress(limit=50):
    from django.db import transaction
    from ...advanced_execution_models import AdvancedExecution

    updated = 0
    with transaction.atomic():
        plans = (
            AdvancedExecution.objects.select_for_update(skip_locked=True)
            .filter(
                provider_mode="test",
            )
            .exclude(
                state__in=["awaiting_consents", "ready", "completed", "closed_partial"]
            )
            .order_by("updated_at")[:limit]
        )
        for plan in plans:
            old = plan.state
            refresh(plan, persist=True)
            if old != plan.state:
                plan.revision += 1
            plan.save(update_fields=["state", "revision", "updated_at"])
            updated += 1
    return updated


def initial_payment_allowed(invoice):
    """The normal invoice endpoint also enforces a conditional package threshold."""
    from ...advanced_execution_models import AdvancedExecutionLeg

    if not invoice.billing_period_id or invoice.billing_period.sequence != 1:
        return True
    legs = AdvancedExecutionLeg.objects.filter(
        execution__provider_mode="test", execution__mode="conditional_package"
    )
    leg = legs.filter(lease=invoice.lease).first()
    if leg is None and invoice.lease.renter_company_id:
        booking = invoice.lease.company_tenancy.preparation.booking
        leg = legs.filter(canonical_kind="company", canonical_id=booking.id).first()
    if not leg:
        return True
    peers = list(leg.execution.legs.select_related("lease"))
    if RentalProviderInstruction.objects.filter(
        subject_id__in=[item.id for item in peers], status="unknown"
    ).exists():
        return False
    for peer in peers:
        lease = canonical_lease(peer)
        if lease is None or lease.status not in {"signed", "active"}:
            return False
        if peer.pk != leg.pk and unresolved_payment(lease):
            return False
    return True


def validate_company_preparation(booking, snapshot):
    from ...advanced_execution_models import AdvancedExecutionLeg
    from ..rental_phase2 import RentalConflict

    leg = (
        AdvancedExecutionLeg.objects.filter(
            canonical_kind="company",
            canonical_id=booking.id,
            execution__provider_mode="test",
        )
        .exclude(execution__state="closed_partial")
        .first()
    )
    if not leg:
        return
    terms = leg.specification["terms"]
    expected = {
        "booking_digest": terms["snapshot_digest"],
        "signer_id": terms["signer_id"],
        "payer_id": terms["payer_authorizer_id"],
        "owner_id": terms["owner_id"],
        "starts_on": terms["starts_on"],
        "ends_on_exclusive": terms["ends_on_exclusive"],
        "deposit_minor": terms["deposit_minor"],
        "full_term_rent_minor": terms["full_term_rent_minor"],
    }
    placements = sorted(
        (row["actor_id"], row["property_id"]) for row in terms["placements"]
    )
    current = sorted(
        (row["employee_id"], row["property_id"]) for row in snapshot["placements"]
    )
    if placements != current or any(
        snapshot.get(key) != value for key, value in expected.items()
    ):
        raise RentalConflict(
            "The reviewed execution participants, placements or terms changed.",
            code="execution_snapshot_changed",
        )
