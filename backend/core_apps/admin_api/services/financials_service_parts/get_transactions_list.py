"""Canonical payment attempts and successful refunds, with explicit states."""

from core_apps.features.models import PaymentAttempt, RefundRequest
from .get_financial_summary import money


def get_transactions_list(status_filter=None, search=None):
    rows = []
    for attempt in PaymentAttempt.objects.select_related(
        "invoice__lease__owner", "payer"
    ).order_by("-created_at")[:500]:
        lease = attempt.invoice.lease
        rows.append(
            {
                "id": str(attempt.id),
                "description": f"Payment {attempt.invoice.reference}",
                "landlord": lease.owner.get_full_name if lease else "",
                "tenant": attempt.payer.get_full_name,
                "amount": money(attempt.amount_minor),
                "isPositive": True,
                "status": (
                    "مدفوع"
                    if attempt.payment_status == "captured"
                    else (
                        "معلق"
                        if attempt.payment_status
                        in {"created", "pending", "authorized"}
                        else attempt.payment_status
                    )
                ),
                "canonicalStatus": attempt.payment_status,
                "at": attempt.created_at.isoformat(),
            }
        )
    for refund in (
        RefundRequest.objects.filter(status="succeeded")
        .select_related("lease__owner", "payment_attempt__payer")
        .order_by("-created_at")[:500]
    ):
        rows.append(
            {
                "id": str(refund.id),
                "description": "Confirmed refund",
                "landlord": refund.lease.owner.get_full_name,
                "tenant": refund.payment_attempt.payer.get_full_name,
                "amount": money(-refund.amount_minor),
                "isPositive": False,
                "status": "مسترد",
                "canonicalStatus": refund.status,
                "at": refund.created_at.isoformat(),
            }
        )
    expected = {"paid": "مدفوع", "pending": "معلق", "refunded": "مسترد"}.get(
        status_filter, status_filter
    )
    if expected and expected != "all":
        rows = [row for row in rows if row["status"] == expected]
    if search:
        rows = [
            row
            for row in rows
            if search.casefold()
            in " ".join(str(value) for value in row.values()).casefold()
        ]
    return sorted(rows, key=lambda row: row["at"], reverse=True)
