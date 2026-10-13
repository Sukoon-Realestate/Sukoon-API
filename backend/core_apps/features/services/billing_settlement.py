from django.db.models import Q
from django.utils import timezone
from ..models import AccountSubscription, InvoicePaymentAllocation, LedgerEntry, PaymentReceipt, SubscriptionPlan
from .rental_phase2 import RentalConflict, add_months
from .rental_phase3 import post_ledger_transaction


def settle_purchase(invoice, attempt, provider_reference):
    """Called under the actor and invoice locks in one database transaction."""
    now = timezone.now()
    if invoice.purpose == "subscription":
        snapshot = invoice.purchase_snapshot
        workspace = snapshot["workspace"]
        scopes = ("tenant", "owner", "both") if workspace == "both" else (workspace, "both")
        if AccountSubscription.objects.filter(user=attempt.payer, workspace__in=scopes, cancelled_at__isnull=True, ends_at__gt=now).exists():
            raise RentalConflict("A subscription is already active.", code="subscription_active")
        end_day = add_months(now.date(), snapshot["period_months"])
        ends = now.replace(year=end_day.year, month=end_day.month, day=end_day.day)
        AccountSubscription.objects.create(user=attempt.payer,
            plan=SubscriptionPlan.objects.get(id=snapshot["id"]), invoice=invoice,
            workspace=workspace, starts_at=now, ends_at=ends, plan_snapshot=snapshot)
    else:
        from .billing_advertising import activate_advertising_invoice
        activate_advertising_invoice(invoice, attempt)
    attempt.payment_status = "captured"
    attempt.provider_attempt_id = provider_reference
    attempt.confirmed_at = now
    attempt.settlement_status = "mock"
    attempt.payout_status = "not_applicable"
    attempt.save()
    receipt = PaymentReceipt.objects.create(payment_attempt=attempt, title="Purchase payment receipt")
    InvoicePaymentAllocation.objects.create(invoice=invoice, payment_attempt=attempt,
        amount_minor=attempt.amount_minor, components={invoice.purpose: attempt.amount_minor})
    invoice.status, invoice.applied_minor, invoice.receipt_id = "paid", attempt.amount_minor, receipt.id
    invoice.revision += 1
    invoice.save(update_fields=["status", "applied_minor", "receipt_id", "revision", "updated_at"])
    post_ledger_transaction(reference=f"purchase:{attempt.id}", kind="mock_purchase_capture", invoice=invoice, attempt=attempt,
        entries=[("mock_provider_clearing", LedgerEntry.Direction.DEBIT, attempt.amount_minor),
                 ("purchase_revenue", LedgerEntry.Direction.CREDIT, attempt.amount_minor)],
        metadata={"mode": "mock", "purpose": invoice.purpose})
