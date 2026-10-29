"""Real HTTP/SQL continuations with explicitly simulated signing/payment events."""

from datetime import timedelta
import pytest
from django.db import transaction
from django.utils import timezone
from core_apps.users.models import User
from core_apps.features.tests.test_company_tenancy import (
    cycle,
    person,
    company_setup as base_company_setup,
    rental_participants,
    policy as base_policy,
    command,
    authenticated,
    API,
    agreement,
    signed_agreement,
    active_agreement,
    occupied_agreement,
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
    IdempotencyRecord,
    ReservationHold,
)
from core_apps.features.services.rental_phase2 import add_months
from core_apps.features.services.company import tenancy_projection
from core_apps.features.rental_phase5_views_parts.change_signing_session import (
    complete_change_signature,
)


@pytest.fixture
def policy(db, settings, request):
    configured = base_policy.__wrapped__(db, settings)
    days = getattr(request, "param", 0)
    configured.lifecycle_rules = {**configured.lifecycle_rules, "turnover_days": days}
    configured.save(update_fields=["lifecycle_rules"])
    return configured


@pytest.fixture
def company_setup(rental_participants, policy, settings, request):
    # These fixtures are also imported by continuation/recovery test modules;
    # reuse the original factory without introducing a new fixture dependency.
    configured = base_company_setup.__wrapped__(rental_participants, policy, settings)
    if getattr(request, "param", None) != "single-property":
        return configured
    from core_apps.features.services.company import bookings, offers

    owner, coordinator, approver, company, building, units, _, housing = configured
    offer = offers.create_offer(
        owner,
        {
            "scope": "selected_units",
            "unit_ids": [units[0].id],
            "monthly_rent_minor": 100000,
            "deposit_minor": 20000,
            "publish": True,
            "occupancy_policy": "reserve_capacity_with_notice",
        },
    )
    housing = bookings.update_request(
        coordinator,
        housing.id,
        {
            "expected_revision": housing.revision,
            "starts_on": housing.starts_on,
            "ends_on_exclusive": housing.ends_on_exclusive,
            "headcount": 2,
        },
    )
    # The normal cycle places both independent employees in this exact unit.
    return (
        owner,
        coordinator,
        approver,
        company,
        building,
        [units[0]] * 2,
        offer,
        housing,
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
@pytest.mark.parametrize(
    "policy,company_setup",
    [(0, None), (1, "single-property")],
    indirect=True,
    ids=["no-buffer", "one-day-buffer"],
)
def test_renewal_last_approver_http_acceptance_preserves_invoice_and_receipt(
    occupied_agreement,
    policy,
):
    cycle, item = occupied_agreement
    company = cycle["company"]
    invoice = item.lease.invoices.get()
    original_invoice = dict(RentInvoice.objects.filter(pk=invoice.pk).values().get())
    original_end = item.lease.end_date
    hold = item.preparation.booking.hold
    turnover = policy.lifecycle_rules["turnover_days"]
    assert (original_end - item.lease.start_date).days == 31
    assert hold.blocked_until_exclusive == original_end + timedelta(days=turnover)
    original_locks = list(item.lease.inventory_day_locks.order_by("id").values())
    owned_buffer = item.lease.inventory_day_locks.filter(stay_on=original_end)
    assert owned_buffer.count() == len({p.pk for p in cycle["units"]}) * turnover
    if turnover:
        row = owned_buffer.get()
        assert row.kind == "occupied" and row.hold_id == hold.pk
        assert row.company_change_id is None and row.expires_at is None
        assert row.unit.physical_key == f"property:{cycle['units'][0].id}"
    reservation = CompanyBudgetReservation.objects.get(item=item.preparation.booking)
    original_rent = reservation.rent_minor
    change = proposal(cycle, item)
    item.lease.refresh_from_db()
    proposal_revision = item.lease.revision
    required = change.snapshot["required"]
    order = ("owner", "signer", "payer", "resident_0", "resident_1", "approver")
    assert set(required) == set(order)
    assert len(set(required.values())) == 6
    assert (
        item.preparation.booking.assignments.filter(occupancy_status="occupied").count()
        == 2
    )
    path = API + f"company-tenancies/{item.id}/"

    for index, role in enumerate(order):
        user = User.objects.get(id=required[role])
        # Owner uses the personal owner context; each company participant sends
        # the real selected-role headers, including approver on the final POST.
        selected_role = "employee" if role.startswith("resident_") else role
        actor = (
            authenticated(user)
            if role == "owner"
            else authenticated(user, company=company, role=selected_role)
        )
        detail = actor.get(path)
        assert detail.status_code == 200, (role, detail.data)
        visible = next(
            row for row in detail.data["changes"] if row["id"] == str(change.id)
        )
        assert visible["roles_to_decide"] == [role]
        capability = actor.get(
            API + "planning-capabilities/",
            {
                "capability": "company_housing",
                "action": "respond_change",
                "subject_id": str(item.id),
            },
        )
        assert capability.status_code == 200, (role, capability.data)
        assert "respond_change" in capability.data["allowed_actions"]
        if role == "approver":
            change.refresh_from_db()
            reservation.refresh_from_db()
            assert change.state == "pending" and change.revision == 6
            assert set(change.decisions) == set(order[:-1])
            assert reservation.rent_minor == original_rent
            assert not change.inventory_locks.exists()
        body = command(
            expected_revision=detail.data["revision"],
            change_id=str(change.id),
            digest=visible["digest"],
            role=role,
            decision="accept",
            reason="Independent synthetic renewal review",
        )
        response = actor.post(path + "respond_change/", body, format="json")
        assert response.status_code == 200, (role, response.data)
        assert response.data["resource"]["revision"] == proposal_revision + index + 1

    change.refresh_from_db()
    change.rental_change.refresh_from_db()
    item.lease.refresh_from_db()
    reservation.refresh_from_db()
    assert change.state == "accepted" and change.revision == 7
    assert set(change.decisions) == set(order)
    assert all(value["decision"] == "accept" for value in change.decisions.values())
    assert change.rental_change.status == "accepted"
    assert change.rental_change.revision == 1
    assert not change.rental_change.signing_sessions.exists()
    assert item.lease.revision == proposal_revision + 6
    assert item.lease.end_date == original_end
    assert item.lease.occupancy_status == "occupied"
    assert (
        reservation.rent_minor
        == original_rent + change.snapshot["content"]["rent_delta_minor"]
    )
    assert change.inventory_locks.exists()
    assert not change.inventory_locks.exclude(kind="hold").exists()
    assert (
        list(
            item.lease.inventory_day_locks.filter(
                id__in=[row["id"] for row in original_locks]
            )
            .order_by("id")
            .values()
        )
        == original_locks
    )
    assert item.lease.billing_periods.count() == 1
    assert item.lease.invoices.count() == 1
    assert (
        dict(RentInvoice.objects.filter(pk=invoice.pk).values().get())
        == original_invoice
    )

    receipt = response.data["operation_receipt"]
    record = IdempotencyRecord.objects.get(
        user=user,
        operation="company.tenancy.respond_change",
        request_key=str(body["request_key"]),
    )
    assert str(record.id) == receipt["id"]
    assert (
        str(record.request_subject_id) == str(record.result_subject_id) == str(item.id)
    )
    assert record.result_revision == item.lease.revision == receipt["revision"]
    assert record.recovery_status == receipt["status"] == "confirmed"
    lookup = actor.get(
        API + f"rental-operations/{body['request_key']}/", {"subject_id": str(item.id)}
    )
    assert lookup.status_code == 200, lookup.data
    assert lookup.data["operation_receipt"] == receipt
    detail = actor.get(path)
    assert detail.status_code == 200, detail.data
    assert detail.data["revision"] == item.lease.revision
    assert str(change.id) not in {row["id"] for row in detail.data["changes"]}


@pytest.mark.django_db
@pytest.mark.parametrize("policy", [1], indirect=True)
@pytest.mark.parametrize("outcome", ["withdraw", "sign"])
def test_renewal_preserves_turnover_provenance_and_protects_extended_end(
    active_agreement, policy, outcome
):
    from core_apps.features.services.rental_lifecycle.inventory import assert_available
    from core_apps.features.services.rental_phase2 import RentalConflict

    cycle, item = active_agreement
    hold = item.preparation.booking.hold
    original_hold = ReservationHold.objects.filter(pk=hold.pk).values().get()
    original_locks = list(item.lease.inventory_day_locks.order_by("id").values())
    original_ids = [row["id"] for row in original_locks]
    invoice = item.lease.invoices.values().get()
    original_end = item.lease.end_date
    next_end = add_months(original_end, 1)
    change = proposal(cycle, item)
    reviews(item, change)
    assert change.state == "accepted"
    assert set(change.inventory_locks.values_list("stay_on", flat=True)) == {
        original_end + timedelta(days=offset)
        for offset in range(1, (next_end - original_end).days + 1)
    }
    assert not change.inventory_locks.filter(id__in=original_ids).exists()
    assert not change.inventory_locks.exclude(kind="hold", expires_at=None).exists()
    for prop in cycle["units"]:
        with pytest.raises(RentalConflict) as conflict:
            assert_available(
                prop,
                {"rental_scope": "entire_property"},
                next_end,
                next_end + timedelta(days=1),
            )
        assert conflict.value.get_codes() == "offer_unavailable"

    if outcome == "withdraw":
        response = act(
            item,
            cycle["owner"],
            "withdraw_change",
            change_id=str(change.id),
            reason="Withdraw unsigned synthetic renewal",
        )
        assert response.status_code == 200, response.data
        assert not change.inventory_locks.exists()
        assert (
            list(item.lease.inventory_day_locks.order_by("id").values())
            == original_locks
        )
        assert (
            CompanyBudgetReservation.objects.get(
                item=item.preparation.booking
            ).rent_minor
            == 100000
        )
        for prop in cycle["units"]:
            assert_available(
                prop,
                {"rental_scope": "entire_property"},
                next_end,
                next_end + timedelta(days=1),
            )
    else:
        signatures(item, change)
        assert change.state == "applied" and item.lease.end_date == next_end
        assert not change.inventory_locks.exclude(
            kind="occupied", expires_at=None
        ).exists()
        assert change.inventory_locks.filter(stay_on=next_end).count() == 2
        assert not item.lease.inventory_day_locks.filter(
            stay_on__gte=next_end + timedelta(days=1)
        ).exists()
        assert (
            list(
                item.lease.inventory_day_locks.filter(id__in=original_ids)
                .order_by("id")
                .values()
            )
            == original_locks
        )
        assert item.lease.billing_periods.count() == 2
    assert ReservationHold.objects.filter(pk=hold.pk).values().get() == original_hold
    assert item.lease.invoices.values().get() == invoice


@pytest.mark.django_db
@pytest.mark.parametrize("policy", [1], indirect=True)
@pytest.mark.parametrize("same_lease", [False, True], ids=["external", "own-unsigned"])
def test_conflicting_or_unsigned_turnover_hold_rejects_final_approval_atomically(
    active_agreement, policy, same_lease
):
    from core_apps.features.services.rental_lifecycle.inventory import allocate_days

    cycle, item = active_agreement
    change = proposal(cycle, item)
    next_end = add_months(item.lease.end_date, 1)
    with transaction.atomic():
        external = allocate_days(
            prop=cycle["units"][1],
            snapshot={"rental_scope": "entire_property"},
            offer_id="independent-external-booking",
            starts_on=next_end,
            ends_on=next_end + timedelta(days=1),
            expires_at=timezone.now() + timedelta(days=1),
            lease=item.lease if same_lease else None,
        )
    original = list(RentalInventoryDayLock.objects.order_by("id").values())
    order = ("owner", "signer", "payer", "resident_0", "resident_1", "approver")
    for role in order[:-1]:
        response = act(
            item,
            User.objects.get(id=change.snapshot["required"][role]),
            "respond_change",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role=role,
            decision="accept",
        )
        assert response.status_code == 200, response.data
    item.lease.refresh_from_db()
    revision = item.lease.revision
    actor = authenticated(cycle["approver"], company=cycle["company"], role="approver")
    body = command(
        expected_revision=revision,
        change_id=str(change.id),
        digest=change.snapshot_digest,
        role="approver",
        decision="accept",
        reason="Independent synthetic review",
    )
    response = actor.post(
        API + f"company-tenancies/{item.id}/respond_change/", body, format="json"
    )
    assert response.status_code == 409, response.data
    assert response.data["detail"].code == "offer_unavailable"
    change.refresh_from_db()
    item.lease.refresh_from_db()
    assert change.state == "pending" and change.revision == 6
    assert set(change.decisions) == set(order[:-1])
    assert item.lease.revision == revision
    assert change.reserved_rent_minor == 0 and not change.inventory_locks.exists()
    assert (
        CompanyBudgetReservation.objects.get(item=item.preparation.booking).rent_minor
        == 100000
    )
    assert list(RentalInventoryDayLock.objects.order_by("id").values()) == original
    assert RentalInventoryDayLock.objects.filter(id=external[0].id).exists()
    assert not IdempotencyRecord.objects.filter(
        user=cycle["approver"], request_key=body["request_key"]
    ).exists()


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
    assert result.status_code in {403, 404}, result.data
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
            mandate.refresh_from_db()
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
