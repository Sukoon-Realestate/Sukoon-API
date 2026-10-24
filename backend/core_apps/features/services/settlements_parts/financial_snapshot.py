"""Settlements: financial snapshot."""

from ...models import DepositAgreement, PaymentAttempt
from ..rental_phase3 import invoice_balance_minor


CHARGE_TYPES = {
    "maintenance",
    "rent",
    "utility",
    "claim",
    "deposit_deduction",
    "damage",
    "cleaning",
    "utilities",
    "rent_adjustment",
}


LINE_TYPES = CHARGE_TYPES | {"deposit_return", "refund", "credit", "write_off"}


def financial_snapshot(lease):
    deposit = DepositAgreement.objects.filter(lease=lease).first()
    from ...models import RentalChargeback

    chargebacks = [
        {"id": str(row.id), "revision": row.revision}
        for row in RentalChargeback.objects.filter(
            payment_attempt__invoice__lease=lease
        ).order_by("pkid")
    ]
    from ...models import BillingSourceLink

    source_billing = [
        {"id": str(link.invoice.id), "revision": link.invoice.revision}
        for link in BillingSourceLink.objects.filter(
            source_kind="maintenance",
            source_id__in=lease.maintenance_requests.values("id"),
        )
        .select_related("invoice")
        .order_by("pkid")
    ]
    return {
        **({"source_billing_invoices": source_billing} if source_billing else {}),
        **({"chargebacks": chargebacks} if chargebacks else {}),
        "invoices": [
            {
                "id": str(x.id),
                "revision": x.revision,
                "balance": invoice_balance_minor(x),
            }
            for x in lease.invoices.exclude(
                status__in=["cancelled", "written_off"]
            ).order_by("pkid")
        ],
        "deposit": (
            {"id": str(deposit.id), "revision": deposit.revision} if deposit else None
        ),
        "payments": list(
            PaymentAttempt.objects.filter(invoice__lease=lease)
            .order_by("pkid")
            .values("pkid", "revision", "payment_status", "settlement_status")
        ),
        "refunds": list(
            lease.refund_requests.order_by("pkid").values("pkid", "revision", "status")
        ),
        "payables": list(
            lease.owner_payables.order_by("pkid").values(
                "pkid", "revision", "payout_status", "net_minor"
            )
        ),
        "disputes": list(
            lease.disputes.order_by("pkid").values("pkid", "revision", "status")
        ),
    }
