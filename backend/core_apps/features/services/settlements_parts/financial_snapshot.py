"""Settlements: financial snapshot."""

from ...models import DepositAgreement, PaymentAttempt
from ..rental_phase3 import invoice_balance_minor


CHARGE_TYPES = {
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
    return {
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
