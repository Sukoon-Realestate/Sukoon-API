"""Canonical payment attempts and successful refunds, with explicit states."""

from django.db.models import Q
from core_apps.features.models import PaymentAttempt, RefundRequest
from .get_financial_summary import money


def get_transactions_list(status_filter=None, search=None, *, paginated=False, _ids=None):
    sources = []

    def records(queryset, name, timestamp, prefix):
        if paginated:
            sources.append((name, queryset, timestamp, prefix))
            return ()
        if _ids is not None:
            queryset = queryset.filter(pk__in=_ids.get(name, []))
        return queryset

    rows = []
    expected = {"paid": "مدفوع", "pending": "معلق", "refunded": "مسترد"}.get(
        status_filter, status_filter
    )

    include_payments = expected is None or expected == "all" or expected in {"مدفوع", "معلق"}
    include_refunds = expected is None or expected == "all" or expected == "مسترد"

    if include_payments:
        pay_qs = PaymentAttempt.objects.select_related("invoice__lease__owner", "payer").order_by(
            "-created_at"
        )

        if expected == "مدفوع":
            pay_qs = pay_qs.filter(payment_status="captured")
        elif expected == "معلق":
            pay_qs = pay_qs.filter(payment_status__in={"created", "pending", "authorized"})

        if search:
            s = search.strip()
            pay_qs = pay_qs.filter(
                Q(invoice__reference__icontains=s)
                | Q(payer__first_name__icontains=s)
                | Q(payer__last_name__icontains=s)
                | Q(payer__email__icontains=s)
                | Q(invoice__lease__owner__first_name__icontains=s)
                | Q(invoice__lease__owner__last_name__icontains=s)
                | Q(invoice__lease__owner__email__icontains=s)
            )

        for attempt in records(pay_qs, "payments", "created_at", ""):
            lease = (
                attempt.invoice.lease if hasattr(attempt, "invoice") and attempt.invoice else None
            )
            landlord_name = ""
            if lease and lease.owner:
                landlord_name = lease.owner.get_full_name or lease.owner.email
            tenant_name = ""
            if attempt.payer:
                tenant_name = attempt.payer.get_full_name or attempt.payer.email
            invoice_ref = (
                attempt.invoice.reference
                if hasattr(attempt, "invoice") and attempt.invoice
                else str(attempt.id)
            )
            rows.append(
                {
                    "id": str(attempt.id),
                    "description": f"Payment {invoice_ref}",
                    "landlord": landlord_name,
                    "tenant": tenant_name,
                    "amount": money(attempt.amount_minor),
                    "isPositive": True,
                    "status": (
                        "مدفوع"
                        if attempt.payment_status == "captured"
                        else (
                            "معلق"
                            if attempt.payment_status in {"created", "pending", "authorized"}
                            else attempt.payment_status
                        )
                    ),
                    "canonicalStatus": attempt.payment_status,
                    "at": attempt.created_at.isoformat(),
                }
            )

    if include_refunds:
        refund_qs = (
            RefundRequest.objects.filter(status="succeeded")
            .select_related("lease__owner", "payment_attempt__payer")
            .order_by("-created_at")
        )

        if search:
            s = search.strip()
            refund_qs = refund_qs.filter(
                Q(lease__owner__first_name__icontains=s)
                | Q(lease__owner__last_name__icontains=s)
                | Q(lease__owner__email__icontains=s)
                | Q(payment_attempt__payer__first_name__icontains=s)
                | Q(payment_attempt__payer__last_name__icontains=s)
                | Q(payment_attempt__payer__email__icontains=s)
            )

        for refund in records(refund_qs, "refunds", "created_at", ""):
            landlord_name = ""
            if refund.lease and refund.lease.owner:
                landlord_name = refund.lease.owner.get_full_name or refund.lease.owner.email
            tenant_name = ""
            if refund.payment_attempt and refund.payment_attempt.payer:
                tenant_name = (
                    refund.payment_attempt.payer.get_full_name or refund.payment_attempt.payer.email
                )
            rows.append(
                {
                    "id": str(refund.id),
                    "description": "Confirmed refund",
                    "landlord": landlord_name,
                    "tenant": tenant_name,
                    "amount": money(-refund.amount_minor),
                    "isPositive": False,
                    "status": "مسترد",
                    "canonicalStatus": refund.status,
                    "at": refund.created_at.isoformat(),
                }
            )

    if expected and expected != "all":
        rows = [row for row in rows if row["status"] == expected]
    if paginated:
        from ..history_page import HistoryPage

        return HistoryPage(
            sources,
            lambda ids: get_transactions_list(status_filter=status_filter, search=search, _ids=ids),
        )
    return sorted(rows, key=lambda row: (row["at"], row["id"]), reverse=True)
