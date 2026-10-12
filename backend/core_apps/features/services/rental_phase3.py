import hashlib
import json
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from ..models import (
    BillingPeriod,
    DepositAgreement,
    InvoiceLine,
    InvoicePaymentAllocation,
    LedgerEntry,
    LedgerTransaction,
    Lease,
    OwnerPayable,
    PaymentAttempt,
    PaymentReceipt,
    ProviderWebhookEvent,
    RentInvoice,
    RefundRequest,
    RentalTimelineEvent,
)
from .rental_phase2 import (
    RentalConflict,
    activate_inventory,
    add_months,
    assert_owner_ready,
)


CAIRO = ZoneInfo("Africa/Cairo")


def cairo_instant(day, at_time=time.min):
    return datetime.combine(day, at_time, tzinfo=CAIRO)


def post_ledger_transaction(
    *, reference, kind, entries, lease=None, invoice=None, attempt=None, metadata=None
):
    debit = sum(item[2] for item in entries if item[1] == LedgerEntry.Direction.DEBIT)
    credit = sum(item[2] for item in entries if item[1] == LedgerEntry.Direction.CREDIT)
    if debit != credit or debit <= 0:
        raise ValidationError(
            "Ledger transaction must contain equal positive debits and credits."
        )
    ledger_transaction, created = LedgerTransaction.objects.get_or_create(
        reference=reference,
        defaults={
            "kind": kind,
            "lease": lease,
            "invoice": invoice,
            "payment_attempt": attempt,
            "metadata": metadata or {},
        },
    )
    if created:
        LedgerEntry.objects.bulk_create(
            [
                LedgerEntry(
                    transaction=ledger_transaction,
                    account=account,
                    direction=direction,
                    amount_minor=amount,
                )
                for account, direction, amount in entries
            ]
        )
    return ledger_transaction


@transaction.atomic
def issue_invoice(period):
    period = (
        BillingPeriod.objects.select_for_update()
        .select_related("lease")
        .get(pk=period.pk)
    )
    invoice = RentInvoice.objects.filter(billing_period=period).first()
    if invoice:
        return invoice
    # Only the newly signed workflow combines the first rent and deposit.
    # Historical active leases and their invoice identities stay unchanged.
    combined = period.sequence == 1 and period.lease.status == Lease.Status.SIGNED
    deposit_minor = (
        int(period.lease.terms.get("deposit", {}).get("amount_minor", 0))
        if combined
        else 0
    )
    total = period.amount_minor + deposit_minor
    if combined and DepositAgreement.objects.filter(lease=period.lease).exists():
        raise RentalConflict("A deposit obligation already exists for this agreement.")
    invoice = RentInvoice.objects.create(
        lease=period.lease,
        billing_period=period,
        reference=f"RENT-{period.lease.id.hex[:8].upper()}-{period.sequence:03d}",
        due_date=period.due_at.astimezone(CAIRO).date(),
        due_at=period.due_at,
        period_start=period.start,
        period_end_exclusive=period.end_exclusive,
        amount_minor=total,
        charges_minor=total,
        currency=period.currency,
        exponent=period.exponent,
        status=RentInvoice.Status.DUE,
    )
    InvoiceLine.objects.create(
        invoice=invoice,
        line_type="base_rent",
        description="Base rent",
        amount_minor=period.amount_minor,
        source={
            "billing_period_id": str(period.id),
            "starts_on": str(period.start),
            "ends_on_exclusive": str(period.end_exclusive),
        },
    )
    if combined:
        DepositAgreement.objects.create(
            lease=period.lease,
            invoice=invoice,
            agreed_minor=deposit_minor,
            due_minor=deposit_minor,
        )
        if deposit_minor:
            InvoiceLine.objects.create(
                invoice=invoice,
                line_type="security_deposit",
                description="Security deposit",
                amount_minor=deposit_minor,
                source={"lease_id": str(period.lease.id)},
            )
    period.status = BillingPeriod.Status.ISSUED
    period.save(update_fields=["status", "updated_at"])
    post_ledger_transaction(
        reference=f"invoice-issued:{invoice.id}",
        kind="invoice_issued",
        lease=period.lease,
        invoice=invoice,
        entries=[
            ("tenant_receivable", LedgerEntry.Direction.DEBIT, total),
            (
                "unearned_rent_liability",
                LedgerEntry.Direction.CREDIT,
                total,
            ),
        ],
    )
    return invoice


@transaction.atomic
def generate_billing_schedule(lease):
    lease = Lease.objects.select_for_update().get(pk=lease.pk)
    if lease.billing_periods.exists():
        return lease.billing_periods.all()
    starts_on = lease.start_date
    ends_on = lease.end_date
    activation = lease.activated_at or timezone.now()
    handover_on = lease.terms.get("handover_on", str(starts_on))
    if isinstance(handover_on, str):
        handover_on = datetime.strptime(handover_on, "%Y-%m-%d").date()
    sequence = 1
    cursor = starts_on
    periods = []
    while cursor < ends_on:
        next_anchor = min(add_months(starts_on, sequence), ends_on)
        if sequence == 1:
            issue_at = activation
            handover_deadline = cairo_instant(handover_on, time.max)
            due_at = (
                lease.hold_expires_at
                if lease.status == Lease.Status.SIGNED
                else min(activation + timedelta(hours=48), handover_deadline)
            )
            if due_at <= activation:
                raise RentalConflict(
                    "The agreed handover window is no longer practical.",
                    code="document_changed",
                )
        else:
            issue_at = cairo_instant(cursor) - timedelta(days=7)
            due_at = cairo_instant(cursor, time.max)
        period = BillingPeriod.objects.create(
            lease=lease,
            sequence=sequence,
            start=cursor,
            end_exclusive=next_anchor,
            issue_at=issue_at,
            due_at=due_at,
            amount_minor=lease.rent_amount_minor,
        )
        periods.append(period)
        cursor = next_anchor
        sequence += 1
    if periods:
        issue_invoice(periods[0])
    return lease.billing_periods.all()


def invoice_balance_minor(invoice):
    return max(invoice.charges_minor - invoice.credits_minor - invoice.applied_minor, 0)


def invoice_payment_allowed(user, invoice):
    from ..providers import checkout_available

    lease = invoice.lease
    return bool(
        user
        and user.is_active
        and user.is_verified
        and user.pk == lease.tenant_id
        and checkout_available()
        and not lease.legacy_read_only
        and (
            lease.status
            in {
                Lease.Status.SIGNED,
                Lease.Status.ACTIVE,
                Lease.Status.TERMINATION_PENDING,
            }
            or (
                lease.status in {Lease.Status.ENDED, Lease.Status.CANCELLED}
                and getattr(getattr(lease, "final_settlement", None), "status", "")
                == "accepted"
            )
        )
        and (
            lease.status != Lease.Status.SIGNED
            or (lease.hold_expires_at and lease.hold_expires_at > timezone.now())
        )
        and invoice.status
        in {
            RentInvoice.Status.DUE,
            RentInvoice.Status.OVERDUE,
            RentInvoice.Status.PARTIALLY_PAID,
        }
        and invoice_balance_minor(invoice) > 0
        and not invoice.payment_attempts.filter(
            payment_status__in=["created", "pending", "authorized"]
        ).exists()
    )


def quote_fingerprint(invoice, request_key, amount_minor, expires_at):
    payload = {
        "invoice_id": str(invoice.id),
        "invoice_revision": invoice.revision,
        "request_key": str(request_key),
        "amount_minor": amount_minor,
        "currency": invoice.currency,
        "expires_at": expires_at.isoformat(),
        "policy_version": "rental-policy-v1",
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def payment_attempt_payload(attempt, user=None):
    from ..providers import mock_completion_metadata
    from .refunds import remaining_components

    invoice = attempt.invoice
    receipt = getattr(attempt, "receipt", None)
    refundable_components = remaining_components(attempt)
    refundable = sum(refundable_components.values())
    return {
        **mock_completion_metadata("payment-attempts", attempt.id, attempt.revision),
        "refundable_balance": {
            "amount_minor": refundable,
            "currency": attempt.currency,
            "exponent": attempt.exponent,
        },
        "refundable_allocations": refundable_components,
        "allowed_actions": (
            ["request_refund"]
            if user is not None
            and user.pk == attempt.payer_id
            and attempt.payment_status == "captured"
            and refundable > 0
            else []
        ),
        "blocking_reasons": [],
        "revision": attempt.revision,
        "lease_id": str(invoice.lease.id),
        "payment_attempt_id": str(attempt.id),
        "invoice_id": str(invoice.id),
        "request_key": str(attempt.request_key),
        "quote_id": str(attempt.quote.id),
        "invoice_revision": attempt.invoice_revision,
        "policy_version": attempt.policy_version,
        "quote_fingerprint": attempt.quote_fingerprint,
        "payment_status": attempt.payment_status,
        "failure_code": attempt.failure_code,
        "invoice_status": invoice.status,
        "amount": {
            "amount_minor": attempt.amount_minor,
            "currency": attempt.currency,
            "exponent": attempt.exponent,
        },
        "confirmed_at": (
            attempt.confirmed_at.isoformat() if attempt.confirmed_at else None
        ),
        "receipt_id": str(receipt.id) if receipt else "",
        "payout_status": attempt.payout_status,
        "settlement_status": attempt.settlement_status,
        "updated_at": attempt.updated_at.isoformat(),
    }


def _capture_attempt(attempt):
    if attempt.payment_status == PaymentAttempt.Status.CAPTURED:
        return attempt
    invoice = RentInvoice.objects.select_for_update().get(pk=attempt.invoice_id)
    lease = Lease.objects.select_for_update().get(pk=invoice.lease_id)
    invoice.lease = lease
    if attempt.amount_minor != invoice_balance_minor(invoice):
        raise RentalConflict("Captured amount does not match invoice balance.")
    attempt.payment_status = PaymentAttempt.Status.CAPTURED
    attempt.confirmed_at = timezone.now()
    attempt.revision += 1
    attempt.save(
        update_fields=["payment_status", "confirmed_at", "revision", "updated_at"]
    )
    invoice.applied_minor += attempt.amount_minor
    invoice.status = RentInvoice.Status.PAID
    invoice.revision += 1
    invoice.save(update_fields=["applied_minor", "status", "revision", "updated_at"])
    allocation, _ = InvoicePaymentAllocation.objects.get_or_create(
        payment_attempt=attempt,
        defaults={"invoice": invoice, "amount_minor": attempt.amount_minor},
    )
    post_ledger_transaction(
        reference=f"payment-captured:{attempt.id}",
        kind="payment_captured",
        lease=invoice.lease,
        invoice=invoice,
        attempt=attempt,
        entries=[
            ("psp_clearing", LedgerEntry.Direction.DEBIT, attempt.amount_minor),
            ("tenant_receivable", LedgerEntry.Direction.CREDIT, attempt.amount_minor),
        ],
    )
    if invoice.invoice_type == RentInvoice.InvoiceType.DEPOSIT:
        allocation.components = {"rent": 0, "deposit": attempt.amount_minor}
        allocation.save(update_fields=["components", "updated_at"])
        post_ledger_transaction(
            reference=f"deposit-collected:{attempt.id}",
            kind="deposit_collected",
            lease=invoice.lease,
            invoice=invoice,
            attempt=attempt,
            entries=[
                (
                    "unearned_rent_liability",
                    LedgerEntry.Direction.DEBIT,
                    attempt.amount_minor,
                ),
                (
                    "deposit_liability",
                    LedgerEntry.Direction.CREDIT,
                    attempt.amount_minor,
                ),
            ],
        )
        agreement = getattr(invoice, "deposit_agreement", None)
        if agreement:
            agreement.collected_minor += attempt.amount_minor
            agreement.due_minor = max(
                agreement.agreed_minor - agreement.collected_minor, 0
            )
            agreement.revision += 1
            agreement.save()
        receipt, _ = PaymentReceipt.objects.get_or_create(payment_attempt=attempt)
        invoice.receipt_id = receipt.id
        invoice.save(update_fields=["receipt_id", "updated_at"])
        return attempt
    deposit = (
        DepositAgreement.objects.select_for_update().filter(invoice=invoice).first()
    )
    deposit_minor = min(deposit.due_minor, attempt.amount_minor) if deposit else 0
    rent_minor = attempt.amount_minor - deposit_minor
    if rent_minor < 0 or deposit_minor < 0:
        raise RentalConflict("Invoice allocations do not match the deposit obligation.")
    commission = (
        rent_minor * 1000 // 10000
        if invoice.billing_period and invoice.billing_period.sequence == 1
        else 0
    )
    net = rent_minor - commission
    allocation.components = {"rent": rent_minor, "deposit": deposit_minor}
    allocation.save(update_fields=["components", "updated_at"])
    entries = [
        ("unearned_rent_liability", LedgerEntry.Direction.DEBIT, attempt.amount_minor),
        ("owner_liability", LedgerEntry.Direction.CREDIT, net),
    ]
    if commission:
        entries.append(("commission_reserve", LedgerEntry.Direction.CREDIT, commission))
    if deposit_minor:
        entries.append(
            ("deposit_liability", LedgerEntry.Direction.CREDIT, deposit_minor)
        )
        deposit.collected_minor += deposit_minor
        deposit.due_minor -= deposit_minor
        deposit.revision += 1
        deposit.save(
            update_fields=["collected_minor", "due_minor", "revision", "updated_at"]
        )
    post_ledger_transaction(
        reference=f"payment-allocated:{attempt.id}",
        kind="payment_allocated",
        lease=invoice.lease,
        invoice=invoice,
        attempt=attempt,
        entries=entries,
    )
    if rent_minor:
        OwnerPayable.objects.get_or_create(
            payment_attempt=attempt,
            defaults={
                "invoice": invoice,
                "lease": invoice.lease,
                "billing_period": invoice.billing_period,
                "gross_minor": rent_minor,
                "commission_minor": commission,
                "net_minor": net,
                "blocking_reasons": [
                    "PSP settlement is pending.",
                    "Move-in is not accepted.",
                ],
            },
        )
    receipt, _ = PaymentReceipt.objects.get_or_create(payment_attempt=attempt)
    invoice.receipt_id = receipt.id
    invoice.save(update_fields=["receipt_id", "updated_at"])
    if invoice.billing_period:
        invoice.billing_period.status = BillingPeriod.Status.PAID
        invoice.billing_period.save(update_fields=["status", "updated_at"])
    if (
        lease.status in {Lease.Status.SIGNED, Lease.Status.EXPIRED}
        and invoice.billing_period
        and invoice.billing_period.sequence == 1
    ):
        _activate_after_initial_capture(lease, attempt)
    return attempt


def _activate_after_initial_capture(lease, attempt):
    """Record real captures even when expiry/readiness prevents activation."""
    from rest_framework.exceptions import PermissionDenied

    try:
        if (
            lease.status != Lease.Status.SIGNED
            or not lease.hold_expires_at
            or lease.hold_expires_at <= timezone.now()
        ):
            raise RentalConflict("The payment hold has expired.", code="hold_expired")
        assert_owner_ready(lease.owner, lease.property)
        activate_inventory(lease)
    except (RentalConflict, PermissionDenied) as exc:
        attempt.failure_code = "activation_review_required"
        attempt.save(update_fields=["failure_code", "updated_at"])
        RentalTimelineEvent.objects.create(
            lease=lease,
            kind="activation_blocked",
            label="Captured payment needs review",
            description=str(exc.detail),
            resource_id=attempt.id,
        )
        return
    lease.status = Lease.Status.ACTIVE
    lease.activated_at = timezone.now()
    lease.revision += 1
    lease.save(update_fields=["status", "activated_at", "revision", "updated_at"])
    RentalTimelineEvent.objects.create(
        lease=lease,
        kind="activated",
        label="Agreement activated after payment",
        resource_id=attempt.id,
    )


def _settle_attempt(attempt):
    if attempt.payment_status != PaymentAttempt.Status.CAPTURED:
        return False
    if attempt.settlement_status == "settled":
        return True
    attempt.settlement_status = "settled"
    attempt.revision += 1
    attempt.save(update_fields=["settlement_status", "revision", "updated_at"])
    refunded_before_settlement = sum(
        tx.entries.filter(account="psp_clearing", direction="credit").aggregate(
            total=Sum("amount_minor")
        )["total"]
        or 0
        for tx in LedgerTransaction.objects.filter(
            payment_attempt=attempt, kind="refund"
        )
    )
    net_settlement = attempt.amount_minor - refunded_before_settlement
    if net_settlement:
        post_ledger_transaction(
            reference=f"payment-settled:{attempt.id}",
            kind="payment_settled",
            lease=attempt.invoice.lease,
            invoice=attempt.invoice,
            attempt=attempt,
            entries=[
                ("platform_cash", LedgerEntry.Direction.DEBIT, net_settlement),
                ("psp_clearing", LedgerEntry.Direction.CREDIT, net_settlement),
            ],
        )
    OwnerPayable.objects.filter(payment_attempt=attempt).update(
        settlement_status="settled",
        blocking_reasons=["Move-in is not accepted."],
        updated_at=timezone.now(),
    )
    from ..rental_phase4_views import evaluate_owner_payables

    evaluate_owner_payables(attempt.invoice.lease)
    return True


@transaction.atomic
def process_provider_event(event):
    # Shared order across captures, refunds, settlements and payouts: lease, attempt, event.
    lease_id = PaymentAttempt.objects.values_list("invoice__lease_id", flat=True).get(
        pk=event.payment_attempt_id
    )
    Lease.objects.select_for_update().get(pk=lease_id)
    attempt = PaymentAttempt.objects.select_for_update().get(
        pk=event.payment_attempt_id
    )
    event = ProviderWebhookEvent.objects.select_for_update(of=("self",)).get(
        pk=event.pk
    )
    if event.processed:
        return event
    payload = event.payload
    if (
        payload.get("currency") != attempt.currency
        or int(payload.get("amount_minor", -1)) != attempt.amount_minor
    ):
        raise RentalConflict("Provider amount or currency mismatch.")
    if event.event_type == "payment.captured":
        _capture_attempt(attempt)
        event.processed = True
    elif event.event_type == "payment.settled":
        event.processed = _settle_attempt(attempt)
    elif event.event_type == "payment.failed":
        if attempt.payment_status != PaymentAttempt.Status.CAPTURED:
            attempt.payment_status = PaymentAttempt.Status.FAILED
            attempt.failure_code = str(payload.get("failure_code") or "provider_failed")
            attempt.revision += 1
            attempt.save()
        event.processed = True
    elif event.event_type == "payment.chargeback":
        if attempt.payment_status != PaymentAttempt.Status.CHARGEDBACK:
            amount = int(payload["amount_minor"])
            attempt.payment_status = PaymentAttempt.Status.CHARGEDBACK
            attempt.revision += 1
            attempt.save(update_fields=["payment_status", "revision", "updated_at"])
            invoice = RentInvoice.objects.select_for_update().get(pk=attempt.invoice_id)
            invoice.applied_minor = max(invoice.applied_minor - amount, 0)
            invoice.status = (
                RentInvoice.Status.DUE
                if invoice.applied_minor == 0
                else RentInvoice.Status.PARTIALLY_PAID
            )
            invoice.revision += 1
            invoice.save()
            post_ledger_transaction(
                reference=f"chargeback:{event.provider_event_id}",
                kind="chargeback",
                lease=invoice.lease,
                invoice=invoice,
                attempt=attempt,
                entries=[
                    ("chargeback_receivable", LedgerEntry.Direction.DEBIT, amount),
                    ("platform_cash", LedgerEntry.Direction.CREDIT, amount),
                ],
            )
            OwnerPayable.objects.filter(payment_attempt=attempt).update(
                payout_status="held",
                blocking_reasons=["A chargeback is unresolved."],
                updated_at=timezone.now(),
            )
            invoice.lease.financial_closure_status = (
                invoice.lease.FinancialClosureStatus.OPEN
            )
            invoice.lease.save(update_fields=["financial_closure_status", "updated_at"])
        event.processed = True
    else:
        raise ValidationError({"type": "Unsupported payment provider event."})
    if event.processed:
        event.processed_at = timezone.now()
        event.save(update_fields=["processed", "processed_at", "updated_at"])
    if event.event_type == "payment.captured":
        for pending in ProviderWebhookEvent.objects.filter(
            payment_attempt=attempt,
            event_type="payment.settled",
            processed=False,
        ).order_by("sequence", "created_at"):
            process_provider_event(pending)
    return event
