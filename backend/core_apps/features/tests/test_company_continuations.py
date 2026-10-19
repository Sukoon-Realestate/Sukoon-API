"""Real HTTP/SQL continuations with explicitly simulated signing/payment events."""

from datetime import timedelta
import pytest
from django.db import transaction
from django.utils import timezone
from core_apps.users.models import User
from core_apps.features.tests.test_company_tenancy import (
    cycle,
    person,
    company_setup,
    rental_participants,
    policy,
    command,
    authenticated,
    API,
    agreement,
    signed_agreement,
    active_agreement,
    act,
    expose_unexpected_exceptions,
)
from core_apps.features.models import (
    CompanyBudgetReservation,
    BillingPeriod,
    RentalInventoryDayLock,
    RentInvoice,
    FinalSettlement,
    SettlementAdjustment,
)
from core_apps.features.services.rental_phase2 import add_months
from core_apps.features.services.company import tenancy_projection
from core_apps.features.rental_phase5_views_parts.change_signing_session import (
    complete_change_signature,
)


def proposal(cycle, item, **extra):
    response = act(
        item,
        cycle["owner"],
        "commercial_change",
        kind="renewal",
        effective_on=str(item.lease.end_date),
        ends_on_exclusive=str(add_months(item.lease.end_date, 1)),
        rent_minor=100000,
        reviewer_membership_id=str(cycle["company"].default_approver.id),
        reason="Extend exact company term",
        **extra,
    )
    assert response.status_code == 200, response.data
    return item.changes.get(kind="renewal")


def reviews(item, change):
    for role, identity in change.snapshot["required"].items():
        response = act(
            item,
            User.objects.get(id=identity),
            "respond_change",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role=role,
            decision="accept",
        )
        assert response.status_code == 200, (role, response.data)
    change.refresh_from_db()


def signatures(item, change):
    response = act(
        item,
        item.lease.owner,
        "submit_continuation",
        change_id=str(change.id),
        digest=change.snapshot_digest,
    )
    assert response.status_code == 200, response.data
    for role, identity in change.snapshot["required"].items():
        if role not in {"owner", "signer", "new_owner"}:
            continue
        response = act(
            item,
            User.objects.get(id=identity),
            "sign_continuation",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role=role,
        )
        assert response.status_code == 200, response.data
        session = change.rental_change.signing_sessions.get(signer__id=identity)
        complete_change_signature(session.provider_session_id)
    change.refresh_from_db()
    item.refresh_from_db()
    item.lease.refresh_from_db()


@pytest.mark.django_db
def test_renewal_requires_every_review_then_signatures_and_keeps_old_invoices(
    active_agreement,
):
    cycle, item = active_agreement
    invoice = item.lease.invoices.get()
    previous = dict(RentInvoice.objects.filter(pk=invoice.pk).values().get())
    original_end = item.lease.end_date
    change = proposal(cycle, item)
    assert change.state == "pending" and not change.inventory_locks.exists()
    reviews(item, change)
    assert change.state == "accepted"
    assert set(change.inventory_locks.values_list("property_id", flat=True)) == {
        p.pk for p in cycle["units"]
    }
    assert change.inventory_locks.filter(kind="hold").exists()
    signatures(item, change)
    assert change.state == "applied" and item.lease.end_date == add_months(
        original_end, 1
    )
    assert not change.inventory_locks.exclude(kind="occupied").exists()
    assert dict(RentInvoice.objects.filter(pk=invoice.pk).values().get()) == previous
    assert item.lease.billing_periods.count() == 2
    assert (
        CompanyBudgetReservation.objects.get(item=item.preparation.booking).rent_minor
        == 200000
    )
    assert set(
        item.preparation.booking.assignments.values_list("ends_on_exclusive", flat=True)
    ) == {item.lease.end_date}
    session = change.rental_change.signing_sessions.first()
    complete_change_signature(session.provider_session_id)
    assert item.lease.billing_periods.count() == 2


@pytest.mark.django_db
def test_review_does_not_fake_provider_or_release_occupied_days(
    active_agreement, settings
):
    cycle, item = active_agreement
    original = item.lease.inventory_day_locks.count()
    change = proposal(cycle, item)
    reviews(item, change)
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    result = act(
        item,
        cycle["owner"],
        "submit_continuation",
        change_id=str(change.id),
        digest=change.snapshot_digest,
    )
    assert result.status_code == 409, result.data
    result = act(
        item,
        cycle["owner"],
        "withdraw_change",
        change_id=str(change.id),
        reason="Cancel before any session",
    )
    assert result.status_code == 200, result.data
    assert item.lease.inventory_day_locks.count() == original
    assert (
        CompanyBudgetReservation.objects.get(item=item.preparation.booking).rent_minor
        == 100000
    )


@pytest.mark.django_db
def test_wrong_actor_and_changed_approver_cannot_supply_consent(active_agreement):
    cycle, item = active_agreement
    change = proposal(cycle, item)
    result = act(
        item,
        cycle["coordinator"],
        "respond_change",
        change_id=str(change.id),
        digest=change.snapshot_digest,
        role="signer",
        decision="accept",
    )
    assert result.status_code == 403, result.data
    member = cycle["company"].default_approver
    member.is_approver = False
    member.save()
    result = act(
        item,
        cycle["approver"],
        "respond_change",
        change_id=str(change.id),
        digest=change.snapshot_digest,
        role="approver",
        decision="accept",
    )
    assert result.status_code == 404, result.data


@pytest.mark.django_db
def test_renewal_conflict_on_second_unit_rolls_back_whole_reservation(active_agreement):
    from core_apps.features.services.rental_lifecycle.inventory import allocate_days

    cycle, item = active_agreement
    change = proposal(cycle, item)
    start = item.lease.end_date
    with transaction.atomic():
        allocate_days(
            prop=cycle["units"][1],
            snapshot={"rental_scope": "entire_property"},
            offer_id="external",
            starts_on=start,
            ends_on=add_months(start, 1),
            expires_at=timezone.now() + timedelta(days=1),
        )
    required = list(change.snapshot["required"].items())
    for role, identity in required:
        result = act(
            item,
            User.objects.get(id=identity),
            "respond_change",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role=role,
            decision="accept",
        )
    assert result.status_code == 409, result.data
    assert not change.inventory_locks.exists()
    assert (
        CompanyBudgetReservation.objects.get(item=item.preparation.booking).rent_minor
        == 100000
    )


@pytest.mark.django_db
def test_unknown_signature_is_never_replaced_and_cannot_be_withdrawn(active_agreement):
    cycle, item = active_agreement
    change = proposal(cycle, item)
    reviews(item, change)
    assert (
        act(
            item,
            cycle["owner"],
            "submit_continuation",
            change_id=str(change.id),
            digest=change.snapshot_digest,
        ).status_code
        == 200
    )
    for _ in range(2):
        result = act(
            item,
            cycle["owner"],
            "sign_continuation",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role="owner",
        )
        assert result.status_code == 200, result.data
        change.rental_change.signing_sessions.update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )
    assert change.rental_change.signing_sessions.count() == 1
    assert (
        act(
            item,
            cycle["owner"],
            "withdraw_change",
            change_id=str(change.id),
            reason="Unknown outcome",
        ).status_code
        == 409
    )
    assert change.inventory_locks.exists()


@pytest.mark.django_db
def test_changed_source_preserves_late_signed_fact_without_applying(active_agreement):
    cycle, item = active_agreement
    change = proposal(cycle, item)
    reviews(item, change)
    assert (
        act(
            item,
            cycle["owner"],
            "submit_continuation",
            change_id=str(change.id),
            digest=change.snapshot_digest,
        ).status_code
        == 200
    )
    assert (
        act(
            item,
            cycle["owner"],
            "sign_continuation",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role="owner",
        ).status_code
        == 200
    )
    assignment = item.preparation.booking.assignments.first()
    assignment.revision += 1
    assignment.save()
    session = change.rental_change.signing_sessions.get()
    complete_change_signature(session.provider_session_id)
    session.refresh_from_db()
    change.refresh_from_db()
    assert session.status == "completed" and change.state == "review_required"
    assert change.inventory_locks.exists()
    assert item.lease.billing_periods.count() == 1


@pytest.mark.django_db
def test_ownership_preserves_creditor_and_removes_old_owner_private_access(
    active_agreement,
):
    cycle, item = active_agreement
    old = cycle["owner"]
    incoming = person("incoming-owner")
    invoice = item.lease.invoices.get()
    for prop in cycle["units"]:
        prop.owner = incoming
        prop.is_ownership_verified = True
        prop.save()
    result = act(
        item,
        old,
        "ownership_change",
        new_owner_id=str(incoming.id),
        reason="Verified transfer, prior obligations unchanged",
    )
    assert result.status_code == 200, result.data
    change = item.changes.get(kind="ownership")
    view = authenticated(incoming).get(API + f"company-tenancies/{item.id}/")
    assert view.status_code == 200, view.data
    assert view.data["assignments"] == [] and view.data["invoices"] == []
    reviews(item, change)
    signatures(item, change)
    assert item.lease.owner == incoming
    invoice.refresh_from_db()
    assert invoice.beneficiary == old
    assert (
        authenticated(old).get(API + f"company-tenancies/{item.id}/").status_code == 404
    )
    assert (
        authenticated(old).get(API + f"rent-invoices/{invoice.id}/").status_code == 200
    )
    assert (
        authenticated(old).get(API + "owner-payables/?workspace=owner").data["count"]
        == 1
    )
    new = RentInvoice.objects.create(
        lease=item.lease,
        reference="FUTURE",
        due_date=item.lease.end_date,
        amount_minor=100,
        charges_minor=100,
    )
    assert new.beneficiary == incoming
    assert authenticated(old).get(API + f"rent-invoices/{new.id}/").status_code == 404


@pytest.mark.django_db
def test_amendment_rejects_issued_obligation_before_review(active_agreement):
    cycle, item = active_agreement
    result = act(
        item,
        cycle["owner"],
        "commercial_change",
        kind="amendment",
        effective_on=str(item.lease.start_date),
        ends_on_exclusive=str(item.lease.end_date),
        rent_minor=80000,
        reviewer_membership_id=str(cycle["company"].default_approver.id),
        reason="Change issued rent",
    )
    assert result.status_code == 409, result.data
    assert not item.changes.exists()


@pytest.mark.django_db
def test_future_amendment_changes_only_unissued_period(active_agreement):
    cycle, item = active_agreement
    change = proposal(cycle, item)
    reviews(item, change)
    signatures(item, change)
    future = item.lease.billing_periods.get(sequence=2)
    original = item.lease.invoices.get()
    amount = original.charges_minor
    result = act(
        item,
        cycle["owner"],
        "commercial_change",
        kind="amendment",
        effective_on=str(future.start),
        ends_on_exclusive=str(future.end_exclusive),
        rent_minor=80000,
        reviewer_membership_id=str(cycle["company"].default_approver.id),
        reason="Agreed unissued-period reduction",
    )
    assert result.status_code == 200, result.data
    amended = item.changes.get(kind="amendment")
    reviews(item, amended)
    signatures(item, amended)
    assert amended.state == "applied"
    future.refresh_from_db()
    original.refresh_from_db()
    assert future.amount_minor == 80000 and original.charges_minor == amount
    assert (
        CompanyBudgetReservation.objects.get(item=item.preparation.booking).rent_minor
        == 180000
    )


@pytest.mark.django_db
def test_budget_reduction_before_final_consent_rejects_without_allocating(
    active_agreement,
):
    cycle, item = active_agreement
    change = proposal(cycle, item)
    cycle["company"].budget_limit_minor = 150000
    cycle["company"].save()
    for role, identity in change.snapshot["required"].items():
        result = act(
            item,
            User.objects.get(id=identity),
            "respond_change",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role=role,
            decision="accept",
        )
    assert result.status_code == 409, result.data
    assert not change.inventory_locks.exists()


@pytest.mark.django_db
def test_settlement_adjustment_additive_independent_and_replay_safe(active_agreement):
    from unittest.mock import patch
    from core_apps.features.tests.test_company_tenancy import handover
    from core_apps.features.services.refunds import execute_refund
    from core_apps.features.services.private_rental_documents import generate
    from core_apps.features.models import RentalDocument

    cycle, item = active_agreement
    day = item.lease.start_date
    with patch("django.utils.timezone.localdate", return_value=day):
        result = act(
            item,
            cycle["owner"],
            "terminate",
            effective_on=str(day),
            reason="End before possession",
        )
        assert result.status_code == 200, result.data
        reviews(item, item.changes.get(kind="termination"))
        handover(cycle, item, "move_out", day)
        assert (
            act(
                item, cycle["payer"], "settlement", reason="Return deposit", lines=[]
            ).status_code
            == 200
        )
        reviews(item, item.changes.get(kind="settlement"))
        for refund in item.lease.refund_requests.all():
            execute_refund(refund)
        original = FinalSettlement.objects.get(lease=item.lease)
        frozen = dict(FinalSettlement.objects.filter(pk=original.pk).values().get())
        operator = User.objects.get(email="execution-reviewer@company-test.invalid")
        line = {
            "id": "correction",
            "type": "utility",
            "description": "Agreed utility correction",
            "amount": {"amount_minor": 500, "currency": "EGP", "exponent": 2},
        }
        bad = act(
            item,
            cycle["payer"],
            "settlement_adjustment",
            lines=[line],
            financial_reviewer_id=str(cycle["owner"].id),
            reason="Not independent",
        )
        assert bad.status_code == 403, bad.data
        for mandate in cycle["mandates"]:
            mandate.limit_minor = 120100
            mandate.save()
        insufficient = act(
            item,
            cycle["payer"],
            "settlement_adjustment",
            lines=[line],
            financial_reviewer_id=str(operator.id),
            reason="Exceeds verified authority",
        )
        assert insufficient.status_code == 409, insufficient.data
        for mandate in cycle["mandates"]:
            mandate.limit_minor = 1000000
            mandate.save()
        result = act(
            item,
            cycle["payer"],
            "settlement_adjustment",
            lines=[line],
            financial_reviewer_id=str(operator.id),
            reason="Correct omitted utility obligation",
        )
        assert result.status_code == 200, result.data
        correction = item.changes.get(kind="settlement_adjustment")
        private = authenticated(operator).get(API + f"company-tenancies/{item.id}/")
        assert private.status_code == 200, private.data
        assert private.data["assignments"] == [] and private.data["invoices"] == []
        reviews(item, correction)
        assert correction.state == "applied"
        adjustment = SettlementAdjustment.objects.get(original=original)
        assert adjustment.execution_status == "executed"
        assert (
            RentInvoice.objects.get(reference=f"SET-{adjustment.id.hex}").amount_minor
            == 500
        )
        assert (
            dict(FinalSettlement.objects.filter(pk=original.pk).values().get())
            == frozen
        )
        from core_apps.features.services.settlements import execute_settlement

        execute_settlement(adjustment)
        assert (
            RentInvoice.objects.filter(reference=f"SET-{adjustment.id.hex}").count()
            == 1
        )
        document = RentalDocument.objects.create(
            lease=item.lease, requested_by=cycle["payer"], document_type="settlement"
        )
        assert generate(document)
        assert str(adjustment.id).encode() in bytes(document.private_content)


@pytest.mark.django_db(transaction=True)
def test_billing_racing_signed_amendment_never_disagrees_with_invoice(active_agreement):
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls
    from core_apps.features.tasks_parts.expire_rental_sources_and_holds import (
        run_rental_billing_cycle,
    )

    cycle, item = active_agreement
    renewal = proposal(cycle, item)
    reviews(item, renewal)
    signatures(item, renewal)
    period = item.lease.billing_periods.get(sequence=2)
    result = act(
        item,
        cycle["owner"],
        "commercial_change",
        kind="amendment",
        effective_on=str(period.start),
        ends_on_exclusive=str(period.end_exclusive),
        rent_minor=80000,
        reviewer_membership_id=str(cycle["company"].default_approver.id),
        reason="Concurrent billing verification",
    )
    assert result.status_code == 200, result.data
    change = item.changes.get(kind="amendment")
    reviews(item, change)
    assert (
        act(
            item,
            cycle["owner"],
            "submit_continuation",
            change_id=str(change.id),
            digest=change.snapshot_digest,
        ).status_code
        == 200
    )
    for role in ["owner", "signer"]:
        assert (
            act(
                item,
                cycle[role],
                "sign_continuation",
                change_id=str(change.id),
                digest=change.snapshot_digest,
                role=role,
            ).status_code
            == 200
        )
    owner_session = change.rental_change.signing_sessions.get(signer=cycle["owner"])
    signer_session = change.rental_change.signing_sessions.get(signer=cycle["signer"])
    complete_change_signature(owner_session.provider_session_id)
    period.issue_at = timezone.now() - timedelta(minutes=1)
    period.save()
    parallel_calls(
        lambda index: (
            complete_change_signature(signer_session.provider_session_id)
            if index == 0
            else run_rental_billing_cycle()
        )
    )
    period.refresh_from_db()
    change.refresh_from_db()
    invoice = RentInvoice.objects.get(billing_period=period)
    assert invoice.amount_minor == period.amount_minor
    assert (change.state, invoice.amount_minor) in {
        ("applied", 80000),
        ("review_required", 100000),
    }
    assert RentInvoice.objects.filter(billing_period=period).count() == 1
