"""Canonical chargeback facts use synthetic provider events and isolated databases."""

import uuid
import pytest
from django.db import transaction
from django.core.exceptions import ValidationError as ModelValidationError
from core_apps.features.models import (
    OwnerPayable,
    RentalChargeback,
    ChargebackRestoration,
    PaymentAttempt,
    RefundRequest,
    LedgerTransaction,
    RentalOperationalCase,
    FinalSettlement,
)
from core_apps.features.rental_phase4_views_parts.handover_respond import (
    evaluate_owner_payables,
)
from core_apps.features.services.rental_phase3 import process_provider_event
from core_apps.features.tests.test_rental_phase3 import phase3_lease
from core_apps.features.tests.test_rental_lifecycle_safety import checkout, event
from core_apps.features.tests.test_rental_lifecycle_safety import operator
from core_apps.features.tests.test_rental_phase3 import client_for
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.services.chargebacks.projection import blockers, totals
from core_apps.features.services.refunds import execute_refund

API = "/api/v1/features/v1/"


@pytest.fixture
def disputed(phase3_lease):
    _, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    process_provider_event(event(attempt, "captured"))
    process_provider_event(event(attempt, "settled"))
    opening = event(attempt, "chargeback")
    process_provider_event(opening)
    return RentalChargeback.objects.get(payment_attempt=attempt)


def fact(item, kind, *, apply=True, verified=True, **values):
    row = event(item.payment_attempt, "chargeback." + kind, verified=verified)
    row.payload = {
        **row.payload,
        "chargeback_event_id": item.opening_event.provider_event_id,
        **values,
    }
    row.save()
    if apply:
        process_provider_event(row)
        row.refresh_from_db()
    item.refresh_from_db()
    return row


def restore(item, **values):
    return fact(
        item,
        "restored",
        funds_status="received",
        cash_reference=str(uuid.uuid4()),
        **values,
    )


def replacement(item):
    invoice = item.payment_attempt.invoice
    invoice.refresh_from_db()
    client = client_for(item.payment_attempt.payer)
    quote = client.post(
        API + f"rent-invoices/{invoice.id}/quote/",
        {
            "action": "quote",
            "expected_revision": invoice.revision,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert quote.status_code == 201, quote.data
    checkout_result = client.post(
        API + f"rent-invoices/{invoice.id}/checkout/",
        {
            "invoice_id": str(invoice.id),
            "expected_revision": invoice.revision,
            "request_key": str(uuid.uuid4()),
            "quote_id": quote.data["resource"]["quote_id"],
        },
        format="json",
    )
    assert checkout_result.status_code == 201, checkout_result.data
    return PaymentAttempt.objects.get(
        id=checkout_result.data["resource"]["payment_attempt_id"]
    )


def approve(item, refund, user=None, body=None):
    user = user or operator("financial_approver")
    item.refresh_from_db()
    body = body or {
        "request_key": str(uuid.uuid4()),
        "expected_revision": item.revision,
        "action": "approve_excess_refund",
        "refund_id": str(refund.id),
        "reason": "Review exact synthetic restored excess.",
    }
    return (
        client_for(user).post(
            API + f"operator/chargebacks/{item.id}/", body, format="json"
        ),
        user,
        body,
    )


@pytest.mark.django_db
def test_won_without_received_cash_does_not_pay_invoice_or_resolve(disputed):
    from core_apps.features.services.chargebacks.projection import payload

    item = disputed
    fact(item, "decided", outcome="won")
    item.payment_attempt.invoice.refresh_from_db()
    assert item.payment_attempt.invoice.applied_minor == 0
    assert item.resolved_at is None and blockers(item)
    assert not item.restorations.exists()
    result = payload(item)
    assert result["resolved"] is False and result["resolved_at"] is None
    assert result["remaining_funding_minor"] == item.amount_minor


@pytest.mark.django_db
def test_restored_cash_closes_original_chargeback_without_second_allocation(disputed):
    from core_apps.features.services.chargebacks.projection import payload

    item = disputed
    fact(item, "decided", outcome="won")
    restore(item)
    invoice = item.payment_attempt.invoice
    invoice.refresh_from_db()
    item.payment_attempt.refresh_from_db()
    assert item.payment_attempt.payment_status == "chargedback"
    assert invoice.applied_minor == item.amount_minor and invoice.status == "paid"
    assert not blockers(item) and item.resolved_at
    result = payload(item)
    assert result["resolved"] is True and result["resolved_at"]
    assert result["remaining_funding_minor"] == 0
    assert OwnerPayable.objects.filter(invoice=invoice).count() == 1
    assert (
        LedgerTransaction.objects.filter(
            invoice=invoice, kind="payment_allocated"
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_lost_requires_real_replacement_and_settlement_not_a_note(disputed):
    item = disputed
    fact(item, "decided", outcome="lost")
    assert blockers(item)
    paid = replacement(item)
    process_provider_event(event(paid, "captured"))
    item.refresh_from_db()
    assert blockers(item) and item.resolved_at is None
    process_provider_event(event(paid, "settled"))
    item.refresh_from_db()
    assert not blockers(item) and item.resolved_at
    assert OwnerPayable.objects.filter(invoice=paid.invoice).count() == 1
    assert (
        LedgerTransaction.objects.filter(
            invoice=paid.invoice, kind="payment_allocated"
        ).count()
        == 1
    )
    assert totals(item)["replacement_settled"] == item.amount_minor


@pytest.mark.django_db
@pytest.mark.parametrize("restore_first", [False, True])
def test_late_cash_and_replacement_create_exact_excess_refund_without_overpayment(
    disputed, restore_first
):
    item = disputed
    fact(item, "decided", outcome="won")
    paid = replacement(item)
    if restore_first:
        restore(item)
    process_provider_event(event(paid, "captured"))
    process_provider_event(event(paid, "settled"))
    if not restore_first:
        restore(item)
    invoice = paid.invoice
    invoice.refresh_from_db()
    assert invoice.applied_minor == invoice.charges_minor
    assert OwnerPayable.objects.filter(invoice=invoice).count() == 1
    refund = RefundRequest.objects.get(lease=invoice.lease, purpose="chargeback_excess")
    assert refund.amount_minor == item.amount_minor and refund.status == "requested"
    assert blockers(item)
    response, _, _ = approve(item, refund)
    assert response.status_code == 200, response.data
    refund = execute_refund(refund)
    assert refund.status == "succeeded"
    item.refresh_from_db()
    invoice.refresh_from_db()
    assert not blockers(item) and item.resolved_at
    assert invoice.applied_minor == invoice.charges_minor
    assert (
        LedgerTransaction.objects.filter(reference=f"refund:{refund.id}").count() == 1
    )
    execute_refund(refund)
    assert (
        LedgerTransaction.objects.filter(reference=f"refund:{refund.id}").count() == 1
    )


@pytest.mark.django_db
def test_duplicate_cash_reference_and_conflicting_identity_are_bounded(disputed):
    item = disputed
    receipt = restore(item, amount_minor=item.amount_minor // 2)
    duplicate = fact(item, "restored", **receipt.payload)
    assert duplicate.processed and item.restorations.count() == 1
    with pytest.raises(RentalConflict), transaction.atomic():
        fact(item, "restored", **{**receipt.payload, "amount_minor": item.amount_minor})
    assert item.restorations.count() == 1
    with pytest.raises(RentalConflict), transaction.atomic():
        fact(item, "decided", outcome="won", chargeback_event_id="wrong-original")


@pytest.mark.django_db
def test_unsigned_final_fact_cannot_create_money(disputed):
    with pytest.raises(RentalConflict), transaction.atomic():
        fact(
            disputed,
            "restored",
            verified=False,
            funds_status="received",
            cash_reference="untrusted",
        )
    assert not disputed.restorations.exists()


@pytest.mark.django_db
def test_original_source_fields_are_immutable(disputed):
    disputed.amount_minor += 1
    with pytest.raises(ModelValidationError):
        disputed.save()


@pytest.mark.django_db
def test_case_closure_cannot_skip_chargeback_funding(disputed):
    from core_apps.features.services.rental_lifecycle.case_commands import act_on_case

    item = disputed
    reviewer = operator("financial_approver")
    case = RentalOperationalCase.objects.get(
        kind="chargeback", payment_attempt=item.payment_attempt
    )
    case.assigned_to = reviewer
    case.save()
    with pytest.raises(RentalConflict), transaction.atomic():
        act_on_case(
            reviewer,
            case.id,
            {
                "request_key": str(uuid.uuid4()),
                "expected_revision": case.revision,
                "action": "resolve",
                "resolution_code": "no_action_required",
                "reason": "Cannot erase real funding.",
            },
        )
    fact(item, "decided", outcome="won")
    restore(item)
    case.refresh_from_db()
    result, _ = act_on_case(
        reviewer,
        case.id,
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": case.revision,
            "action": "resolve",
            "resolution_code": "corrected",
            "reason": "Canonical provider cash was restored.",
        },
    )
    assert result["resource"]["status"] == "resolved"


@pytest.mark.django_db
def test_excess_approval_is_independent_replay_safe_and_provider_absence_retains_debt(
    disputed, settings
):
    item = disputed
    fact(item, "decided", outcome="won")
    paid = replacement(item)
    process_provider_event(event(paid, "captured"))
    process_provider_event(event(paid, "settled"))
    restore(item)
    refund = RefundRequest.objects.get(purpose="chargeback_excess")
    owner = item.payment_attempt.invoice.lease.owner
    owner.is_staff = owner.is_superuser = True
    owner.save()
    response, _, _ = approve(item, refund, user=owner)
    assert response.status_code == 403
    item.refresh_from_db()
    response, reviewer, body = approve(
        item,
        refund,
        body={
            "request_key": str(uuid.uuid4()),
            "expected_revision": str(item.revision),
            "action": "approve_excess_refund",
            "refund_id": str(refund.id),
            "reason": "Reviewed evidenced excess with a serialized numeric revision.",
        },
    )
    assert response.status_code == 200, response.data
    replay, _, _ = approve(
        item,
        refund,
        reviewer,
        {**body, "expected_revision": int(body["expected_revision"])},
    )
    assert replay.status_code == 200 and replay.data == response.data
    reviewer.sensitive_actions_frozen = True
    reviewer.save()
    revoked, _, _ = approve(item, refund, reviewer, body)
    assert revoked.status_code == 403
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = False
    with pytest.raises(RentalConflict), transaction.atomic():
        execute_refund(refund)
    refund.refresh_from_db()
    assert refund.status == "approved" and blockers(item)


@pytest.mark.django_db
@pytest.mark.parametrize("resolution", ["full_restoration", "overlap_then_replacement"])
def test_prior_refund_overlap_is_not_recharged_or_restored_twice(
    phase3_lease, resolution
):
    _, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    process_provider_event(event(attempt, "captured"))
    process_provider_event(event(attempt, "settled"))
    amount = attempt.amount_minor // 5
    old_refund = RefundRequest.objects.create(
        lease=lease,
        payment_attempt=attempt,
        requester=tenant,
        approved_by=lease.owner,
        amount_minor=amount,
        refundable_balance_snapshot_minor=attempt.amount_minor,
        request_key=uuid.uuid4(),
        reason="Earlier synthetic authorized refund",
        allocations={"rent": amount, "deposit": 0},
        status="approved",
    )
    execute_refund(old_refund)
    process_provider_event(event(attempt, "chargeback"))
    item = RentalChargeback.objects.get(payment_attempt=attempt)
    assert item.prior_refund_overlap_minor == amount
    if resolution == "full_restoration":
        fact(item, "decided", outcome="won")
        restore(item)
    else:
        fact(item, "decided", outcome="lost")
        attempt.invoice.refresh_from_db()
        client = client_for(tenant)
        path = API + f"rent-invoices/{attempt.invoice.id}/quote/"
        quote_body = {
            "action": "quote",
            "expected_revision": attempt.invoice.revision,
            "request_key": str(uuid.uuid4()),
        }
        assert client.post(path, quote_body, format="json").status_code == 409
        restore(item, amount_minor=amount)
        quote = client.post(
            path, {**quote_body, "request_key": str(uuid.uuid4())}, format="json"
        )
        assert quote.status_code == 201, quote.data
        disclosure = quote.data["resource"]["chargeback_replacement"]
        assert disclosure["original_funding_minor"] == attempt.amount_minor - amount
        assert disclosure["quote_total_minor"] == attempt.amount_minor - amount
        assert disclosure["remaining_invoice_minor"] == amount
        assert disclosure["excess_refund_minor"] == 0
        paid = replacement(item)
        assert paid.amount_minor == attempt.amount_minor - amount
        process_provider_event(event(paid, "captured"))
        process_provider_event(event(paid, "settled"))
        item.refresh_from_db()
    attempt.invoice.refresh_from_db()
    assert attempt.invoice.applied_minor == attempt.amount_minor - amount
    assert not item.restorations.exclude(excess_minor=0).exists()
    assert not blockers(item)
    if resolution == "overlap_then_replacement":
        assert not RefundRequest.objects.filter(purpose="chargeback_excess").exists()
        next_payment = replacement(item)
        assert next_payment.amount_minor == amount
        process_provider_event(event(next_payment, "captured"))
        attempt.invoice.refresh_from_db()
        assert attempt.invoice.applied_minor == attempt.amount_minor
        assert OwnerPayable.objects.filter(invoice=attempt.invoice).count() == 2


@pytest.mark.django_db(transaction=True)
def test_replacement_capture_and_cash_restoration_serialize_without_overpayment(
    disputed,
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import close_old_connections
    from core_apps.features.models import ProviderWebhookEvent

    item = disputed
    fact(item, "decided", outcome="won")
    paid = replacement(item)
    captured = event(paid, "captured")
    restored = fact(
        item,
        "restored",
        apply=False,
        funds_status="received",
        cash_reference="race-restoration",
    )
    barrier = Barrier(2)

    def apply(identity):
        close_old_connections()
        try:
            row = ProviderWebhookEvent.objects.get(pk=identity)
            barrier.wait(timeout=10)
            process_provider_event(row)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(apply, [captured.pk, restored.pk]))
    paid.invoice.refresh_from_db()
    assert paid.invoice.applied_minor == paid.invoice.charges_minor
    assert RefundRequest.objects.filter(purpose="chargeback_excess").count() == 1
    assert OwnerPayable.objects.filter(invoice=paid.invoice).count() == 1


@pytest.mark.django_db
def test_full_dispute_rejects_partial_or_second_episode_without_new_effect(disputed):
    item = disputed
    before = LedgerTransaction.objects.count()
    row = event(item.payment_attempt, "chargeback")
    row.payload = {**row.payload, "amount_minor": item.amount_minor // 2}
    row.save()
    with pytest.raises(RentalConflict), transaction.atomic():
        process_provider_event(row)
    row.payload = {
        **row.payload,
        "amount_minor": item.amount_minor,
        "dispute_id": "new-episode",
    }
    row.save()
    with pytest.raises(RentalConflict), transaction.atomic():
        process_provider_event(row)
    row.payload = {"currency": item.currency, "amount_minor": item.amount_minor}
    row.save()
    with pytest.raises(RentalConflict), transaction.atomic():
        process_provider_event(row)
    assert LedgerTransaction.objects.count() == before


@pytest.mark.django_db
def test_replacement_refund_reduces_retained_funding_and_original_payable_once(
    disputed,
):
    from core_apps.features.services.chargebacks.projection import funding_ready

    item = disputed
    fact(item, "decided", outcome="lost")
    paid = replacement(item)
    process_provider_event(event(paid, "captured"))
    process_provider_event(event(paid, "settled"))
    item.refresh_from_db()
    refund = RefundRequest.objects.create(
        lease=paid.invoice.lease,
        payment_attempt=paid,
        requester=paid.payer,
        amount_minor=paid.amount_minor,
        refundable_balance_snapshot_minor=paid.amount_minor,
        request_key=uuid.uuid4(),
        reason="An independent subsequent authorized full reversal.",
        allocations=paid.invoice_allocation.components,
        status="approved",
    )
    execute_refund(refund)
    item.refresh_from_db()
    value = totals(item)
    assert value["retained_funding"] == value["required_funding"] == 0
    assert not funding_ready(item.payment_attempt)
    payable = OwnerPayable.objects.get(payment_attempt=item.payment_attempt)
    assert payable.net_minor == 0 and payable.payout_status == "cancelled"
    paid.invoice.refresh_from_db()
    assert paid.invoice.applied_minor == 0 and paid.invoice.status == "due"
    assert (
        item.resolved_at is not None
    )  # Provider case is final; the returned payment creates ordinary invoice debt.
    next_payment = replacement(item)
    process_provider_event(event(next_payment, "captured"))
    assert OwnerPayable.objects.filter(invoice=paid.invoice).count() == 2
    assert (
        OwnerPayable.objects.get(payment_attempt=next_payment).net_minor
        == paid.invoice_allocation.components["rent"] * 9 // 10
    )


@pytest.mark.django_db
def test_admin_review_is_reachable_and_does_not_execute_money(
    disputed, client, settings
):
    from django.urls import reverse

    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    item = disputed
    fact(item, "decided", outcome="won")
    paid = replacement(item)
    process_provider_event(event(paid, "captured"))
    process_provider_event(event(paid, "settled"))
    restore(item)
    refund = RefundRequest.objects.get(purpose="chargeback_excess")
    reviewer = operator("financial_approver")
    client.force_login(reviewer)
    listing = client.get(reverse("admin:features_rentalchargeback_changelist"))
    assert listing.status_code == 200
    assert b"Inspect original evidence" in listing.content
    path = reverse("admin:chargeback-review", args=[item.pk])
    view = client.get(path)
    assert view.status_code == 200
    assert b"Approve exact excess refund" in view.content
    read_only_reviewer = operator("psp_reconciliation")
    client.force_login(read_only_reviewer)
    read_only_view = client.get(path)
    assert read_only_view.status_code == 200
    assert b"Approve exact excess refund" not in read_only_view.content
    client.force_login(reviewer)
    item.refresh_from_db()
    accepted = client.post(
        path,
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": item.revision,
            "action": "approve_excess_refund",
            "refund_id": str(refund.id),
            "reason": "Inspect original provider and excess evidence.",
        },
    )
    assert accepted.status_code == 302
    refund.refresh_from_db()
    assert refund.status == "approved" and not refund.provider_refund_id
    owner = item.payment_attempt.invoice.lease.owner
    owner.is_staff = owner.is_superuser = True
    owner.save()
    client.force_login(owner)
    assert client.get(path).status_code == 403
    assert client.post(path, {}).status_code == 403


@pytest.mark.django_db
def test_final_fact_before_opening_replays_only_after_exact_original_evidence(
    phase3_lease,
):
    from core_apps.features.models import ProviderWebhookEvent

    _, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    process_provider_event(event(attempt, "captured"))
    opening = event(attempt, "chargeback")
    decision = event(attempt, "chargeback.decided")
    decision.payload = {
        **decision.payload,
        "chargeback_event_id": opening.provider_event_id,
        "outcome": "won",
    }
    decision.save()
    process_provider_event(decision)
    decision.refresh_from_db()
    assert not decision.processed
    process_provider_event(opening)
    decision.refresh_from_db()
    item = RentalChargeback.objects.get(payment_attempt=attempt)
    assert decision.processed and item.outcome == "won"
    restore(item)
    assert item.resolved_at is None  # The earlier original settlement is still unknown.
    process_provider_event(event(attempt, "settled"))
    item.refresh_from_db()
    assert not blockers(item) and item.resolved_at


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payout_state", ["submitted", "processing", "succeeded", "cancelled"]
)
def test_chargeback_preserves_original_payout_history(phase3_lease, payout_state):
    _, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    process_provider_event(event(attempt, "captured"))
    OwnerPayable.objects.filter(payment_attempt=attempt).update(
        payout_status=payout_state
    )
    process_provider_event(event(attempt, "chargeback"))
    with transaction.atomic():
        evaluate_owner_payables(lease)
    assert (
        OwnerPayable.objects.get(payment_attempt=attempt).payout_status == payout_state
    )
    item = RentalChargeback.objects.get(payment_attempt=attempt)
    fact(item, "decided", outcome="won")
    restore(item)
    process_provider_event(event(attempt, "settled"))
    assert (
        OwnerPayable.objects.get(payment_attempt=attempt).payout_status == payout_state
    )


@pytest.mark.django_db
def test_rejected_pending_fact_cannot_prevent_original_debit(phase3_lease):
    _, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    process_provider_event(event(attempt, "captured"))
    opening = event(attempt, "chargeback")
    invalid = event(attempt, "chargeback.decided")
    invalid.payload = {
        **invalid.payload,
        "chargeback_event_id": opening.provider_event_id,
        "outcome": "recovered",
    }
    invalid.save()
    with pytest.raises(RentalConflict), transaction.atomic():
        process_provider_event(invalid)
    process_provider_event(opening)
    item = RentalChargeback.objects.get(payment_attempt=attempt)
    assert (
        item.outcome == "open" and item.payment_attempt.payment_status == "chargedback"
    )
    invalid.refresh_from_db()
    assert not invalid.processed


@pytest.mark.django_db
def test_only_current_independent_finance_can_read_or_replay_approval(disputed):
    from core_apps.users.models import User
    from core_apps.admin_api.models import StaffProfile

    item = disputed
    path = API + f"operator/chargebacks/{item.id}/"
    outsider = User.objects.create_user(
        email="outside-chargeback@example.test", password="pass", is_verified=True
    )
    for actor in (
        outsider,
        item.payment_attempt.payer,
        item.payment_attempt.invoice.lease.owner,
    ):
        assert client_for(actor).get(path).status_code == 403
        assert (
            client_for(actor)
            .get(API + f"operator/chargebacks/{uuid.uuid4()}/")
            .status_code
            == 403
        )
    fact(item, "decided", outcome="won")
    paid = replacement(item)
    process_provider_event(event(paid, "captured"))
    process_provider_event(event(paid, "settled"))
    restore(item)
    refund = RefundRequest.objects.get(purpose="chargeback_excess")
    response, reviewer, body = approve(item, refund)
    assert response.status_code == 200
    mismatched, _, _ = approve(
        item, refund, reviewer, {**body, "reason": "Changed request identity content."}
    )
    assert mismatched.status_code == 409
    StaffProfile.objects.filter(user=reviewer).update(role_name="psp_reconciliation")
    replay, _, _ = approve(item, refund, reviewer, body)
    assert replay.status_code == 403
    StaffProfile.objects.filter(user=reviewer).update(is_active=False)
    assert client_for(reviewer).get(path).status_code == 403
    replay, _, _ = approve(item, refund, reviewer, body)
    assert replay.status_code == 403


@pytest.mark.django_db
def test_approval_rejects_stale_chargeback_revision(disputed):
    item = disputed
    fact(item, "decided", outcome="won")
    paid = replacement(item)
    process_provider_event(event(paid, "captured"))
    process_provider_event(event(paid, "settled"))
    restore(item)
    refund = RefundRequest.objects.get(purpose="chargeback_excess")
    response, _, _ = approve(
        item,
        refund,
        body={
            "request_key": str(uuid.uuid4()),
            "expected_revision": 1,
            "action": "approve_excess_refund",
            "refund_id": str(refund.id),
            "reason": "Outdated review.",
        },
    )
    assert response.status_code == 409
    refund.refresh_from_db()
    assert refund.status == "requested"


@pytest.mark.django_db
def test_all_chargeback_admin_history_requires_current_finance_and_independence(
    disputed, client, settings
):
    from django.contrib.auth.models import Permission
    from django.urls import reverse
    from core_apps.users.models import User
    from core_apps.admin_api.models import StaffProfile

    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    item = disputed
    fact(item, "decided", outcome="won")
    paid = replacement(item)
    process_provider_event(event(paid, "captured"))
    process_provider_event(event(paid, "settled"))
    restore(item)
    records = [item, item.replacement_payments.get(), item.restorations.get()]
    ordinary_staff = User.objects.create_user(
        email="ordinary-admin-chargeback@example.test",
        password="pass",
        is_verified=True,
        is_staff=True,
    )
    ordinary_staff.user_permissions.add(
        *Permission.objects.filter(
            content_type__app_label="features",
            codename__in=[
                "view_rentalchargeback",
                "view_chargebackreplacementpayment",
                "view_chargebackrestoration",
            ],
        )
    )
    reviewer = operator("financial_approver")
    StaffProfile.objects.filter(user=reviewer).update(is_active=False)
    for user in (ordinary_staff, reviewer):
        client.force_login(user)
        for row in records:
            model = row._meta.model_name
            assert (
                client.get(reverse(f"admin:features_{model}_changelist")).status_code
                == 403
            )
            assert (
                client.get(
                    reverse(f"admin:features_{model}_change", args=[row.pk])
                ).status_code
                == 403
            )
        assert (
            client.get(reverse("admin:chargeback-review", args=[item.pk])).status_code
            == 403
        )
    owner = item.payment_attempt.invoice.lease.owner
    owner.is_staff = owner.is_superuser = True
    owner.save()
    client.force_login(owner)
    for row in records:
        model = row._meta.model_name
        listing = client.get(reverse(f"admin:features_{model}_changelist"))
        assert (
            listing.status_code == 200 and str(item.id).encode() not in listing.content
        )
        assert client.get(
            reverse(f"admin:features_{model}_change", args=[row.pk])
        ).status_code in {302, 403, 404}


@pytest.mark.django_db
def test_authenticated_webhook_ingress_final_facts_and_provider_boundary(
    phase3_lease, settings
):
    from rest_framework.test import APIClient
    from core_apps.features.models import ProviderWebhookEvent
    from core_apps.features.providers import sign_fake_webhook

    _, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    client = APIClient()
    path = API + "provider-webhooks/payments/"

    def post(body, signature=None):
        return client.post(
            path,
            body,
            format="json",
            HTTP_X_RENTAL_SIGNATURE=signature or sign_fake_webhook(body),
        )

    base = {
        "payment_attempt_id": str(attempt.id),
        "amount_minor": attempt.amount_minor,
        "currency": attempt.currency,
    }
    for kind in ("captured", "settled", "chargeback"):
        body = {**base, "event_id": "authenticated-" + kind, "type": "payment." + kind}
        response = post(body)
        assert response.status_code == 200, response.data
    item = RentalChargeback.objects.get(payment_attempt=attempt)
    decision = {
        **base,
        "event_id": "authenticated-final",
        "type": "payment.chargeback.decided",
        "chargeback_event_id": "authenticated-chargeback",
        "outcome": "won",
    }
    assert post(decision, "invalid-signature").status_code == 403
    assert not ProviderWebhookEvent.objects.filter(
        provider_event_id=decision["event_id"]
    ).exists()
    assert post(decision).status_code == 200
    item.refresh_from_db()
    assert item.outcome == "won" and item.resolved_at is None
    cash = {
        **base,
        "event_id": "authenticated-cash",
        "type": "payment.chargeback.restored",
        "chargeback_event_id": "authenticated-chargeback",
        "funds_status": "received",
        "cash_reference": "authenticated-bank-reference",
    }
    assert post(cash).status_code == 200
    item.refresh_from_db()
    assert item.resolved_at and item.restorations.count() == 1
    assert post(cash).data["duplicate"] is True
    assert post({**cash, "amount_minor": attempt.amount_minor - 1}).status_code == 409
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = False
    assert post({**cash, "event_id": "unavailable-live-receipt"}).status_code == 404
    assert item.restorations.count() == 1


@pytest.mark.django_db
def test_pending_replacement_refund_reserves_original_payable_before_dispatch(disputed):
    from core_apps.features.models import OwnerPaymentProfile, PayoutBatch, RentalPayout
    from core_apps.features.services.rental_lifecycle.provider_instructions import (
        validate_payout_instruction,
    )

    item = disputed
    fact(item, "decided", outcome="lost")
    paid = replacement(item)
    process_provider_event(event(paid, "captured"))
    process_provider_event(event(paid, "settled"))
    payable = OwnerPayable.objects.get(payment_attempt=item.payment_attempt)
    owner = payable.lease.owner
    profile = OwnerPaymentProfile.objects.create(
        owner=owner,
        status="ready",
        payout_ready=True,
        provider="fake",
        provider_account_id="synthetic-chargeback-payable-beneficiary",
    )
    batch = PayoutBatch.objects.create(
        approved_by=operator("payout_operator"), request_key=uuid.uuid4()
    )
    payout = RentalPayout.objects.create(
        batch=batch,
        owner=owner,
        lease=payable.lease,
        amount_minor=payable.net_minor,
        beneficiary_profile_revision=profile.revision,
        beneficiary_provider=profile.provider,
        beneficiary_account_id=profile.provider_account_id,
    )
    payout.payables.add(payable)
    payout.payables.update(payout_status="submitted")
    validate_payout_instruction(payout)
    RefundRequest.objects.create(
        lease=paid.invoice.lease,
        payment_attempt=paid,
        requester=paid.payer,
        amount_minor=paid.amount_minor,
        refundable_balance_snapshot_minor=paid.amount_minor,
        request_key=uuid.uuid4(),
        reason="Replacement-funded invoice refund awaiting review.",
        allocations=paid.invoice_allocation.components,
    )
    with pytest.raises(RentalConflict) as error:
        validate_payout_instruction(payout)
    assert error.value.get_codes() == "refund_pending"
    assert not payout.provider_payout_id


@pytest.mark.django_db
def test_chargeback_is_not_reenabled_by_payable_recalculation(phase3_lease):
    _, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    process_provider_event(event(attempt, "captured"))
    process_provider_event(event(attempt, "chargeback"))
    with transaction.atomic():
        evaluate_owner_payables(lease)
    payable = OwnerPayable.objects.get(payment_attempt=attempt)
    assert payable.payout_status == "held"
    assert any("chargeback" in reason for reason in payable.blocking_reasons)
