from django.db.models import Q
from django.utils import timezone
from ..models import (
    AccountSubscription,
    InvoicePaymentAllocation,
    LedgerEntry,
    PaymentReceipt,
    SubscriptionPlan,
)
from .rental_phase2 import RentalConflict, add_months
from .rental_phase3 import post_ledger_transaction


def settle_purchase(
    invoice, attempt, provider_reference, *, provider_mode="mock", verified=None
):
    """Called under the actor and invoice locks in one database transaction."""
    now = timezone.now()
    if provider_mode != "hosted":
        fulfill_purchase(
            invoice, attempt, provider_mode=provider_mode, verified=verified
        )
    if attempt.payment_status == "captured":
        return
    attempt.payment_status = "captured"
    attempt.provider_attempt_id = provider_reference
    attempt.confirmed_at = now
    attempt.settlement_status = "mock" if provider_mode == "mock" else "pending"
    attempt.payout_status = "not_applicable"
    attempt.save()
    receipt = PaymentReceipt.objects.create(
        payment_attempt=attempt, title="Purchase payment receipt"
    )
    InvoicePaymentAllocation.objects.create(
        invoice=invoice,
        payment_attempt=attempt,
        amount_minor=attempt.amount_minor,
        components={invoice.purpose: attempt.amount_minor},
    )
    invoice.status, invoice.applied_minor, invoice.receipt_id = (
        "paid",
        attempt.amount_minor,
        receipt.id,
    )
    invoice.revision += 1
    invoice.save(
        update_fields=[
            "status",
            "applied_minor",
            "receipt_id",
            "revision",
            "updated_at",
        ]
    )
    post_ledger_transaction(
        reference=f"purchase:{attempt.id}",
        kind=(
            "mock_purchase_capture"
            if provider_mode == "mock"
            else (
                "hosted_purchase_capture"
                if provider_mode == "hosted"
                else "store_purchase_capture"
            )
        ),
        invoice=invoice,
        attempt=attempt,
        entries=[
            (
                (
                    "mock_provider_clearing"
                    if provider_mode == "mock"
                    else (
                        "psp_clearing"
                        if provider_mode == "hosted"
                        else "store_provider_clearing"
                    )
                ),
                LedgerEntry.Direction.DEBIT,
                attempt.amount_minor,
            ),
            (
                (
                    "service_funds_liability"
                    if invoice.purpose == "maintenance"
                    else "purchase_revenue"
                ),
                LedgerEntry.Direction.CREDIT,
                attempt.amount_minor,
            ),
        ],
        metadata={"mode": provider_mode, "purpose": invoice.purpose},
    )

    if provider_mode == "hosted" and invoice.purpose != "maintenance":
        from ..models import PaymentFulfillment
        from .payment_fulfillment import deliver

        job, _ = PaymentFulfillment.objects.get_or_create(
            invoice=invoice, defaults={"attempt": attempt}
        )
        deliver(job.pk)
    elif provider_mode == "mock":
        from .billing_notifications import record_fulfilled

        record_fulfilled(invoice, attempt)


def fulfill_purchase(invoice, attempt, *, provider_mode="hosted", verified=None):
    now = timezone.now()
    if invoice.purpose == "subscription":
        snapshot = invoice.purchase_snapshot
        workspace = snapshot["workspace"]
        scopes = (
            ("tenant", "owner", "both") if workspace == "both" else (workspace, "both")
        )
        if (
            AccountSubscription.objects.filter(
                **(
                    {"organization": invoice.organization}
                    if invoice.organization_id
                    else {"user": attempt.payer, "organization__isnull": True}
                ),
                workspace__in=scopes,
                store_status__in=["", "active", "grace"],
            )
            .filter(Q(ends_at__gt=now) | Q(store_status="grace", grace_ends_at__gt=now))
            .exists()
        ):
            raise RentalConflict(
                "A subscription is already active.", code="subscription_active"
            )
        end_day = add_months(now.date(), snapshot["period_months"])
        ends = now.replace(year=end_day.year, month=end_day.month, day=end_day.day)
        AccountSubscription.objects.create(
            user=attempt.payer,
            plan=SubscriptionPlan.objects.get(id=snapshot["id"]),
            invoice=invoice,
            workspace=workspace,
            organization=invoice.organization,
            store_platform=(
                "ios"
                if provider_mode == "storekit"
                else "android" if provider_mode == "play_billing" else ""
            ),
            store_status="active" if verified else "",
            auto_renew=verified.auto_renew if verified else False,
            starts_at=verified.purchased_at if verified else now,
            ends_at=verified.expires_at if verified else ends,
            plan_snapshot=snapshot,
        )
    elif invoice.purpose == "promotion":
        from .billing_sources import activate_promotion

        activate_promotion(invoice)
    elif invoice.purpose == "advertising":
        from .billing_advertising import activate_advertising_invoice

        activate_advertising_invoice(invoice, attempt, hosted=provider_mode == "hosted")
