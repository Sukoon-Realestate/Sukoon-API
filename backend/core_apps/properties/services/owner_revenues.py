"""Owner income readback from confirmed payout ledger postings, in EGP."""

from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from django.db.models import Sum
from django.utils import timezone

from core_apps.features.models import LedgerEntry


def owner_revenues(owner, language="ar"):
    arabic = language.startswith("ar")
    currency = "ج" if arabic else "EGP"
    basis = "التحويلات المؤكدة للمالك" if arabic else "Confirmed owner payouts"
    cairo = ZoneInfo("Africa/Cairo")
    today = timezone.localtime(timezone.now(), cairo).date()
    month = today.replace(day=1)
    previous = (month - timedelta(days=1)).replace(day=1)
    following = (month.replace(day=28) + timedelta(days=4)).replace(day=1)

    def boundary(day):
        return datetime.combine(day, time.min, tzinfo=cairo)

    # A posted owner-liability debit is one confirmed payout. Tenant captures,
    # held payables, deposits, asking prices and the balancing cash leg are not income.
    entries = LedgerEntry.objects.filter(
        transaction__lease__owner=owner,
        transaction__kind="owner_payout",
        account="owner_liability",
        direction=LedgerEntry.Direction.DEBIT,
        currency="EGP",
        exponent=2,
    )
    current = entries.filter(
        transaction__created_at__gte=boundary(month),
        transaction__created_at__lt=boundary(following),
    )
    previous_entries = entries.filter(
        transaction__created_at__gte=boundary(previous),
        transaction__created_at__lt=boundary(month),
    )
    total_minor = current.aggregate(value=Sum("amount_minor"))["value"] or 0
    previous_minor = previous_entries.aggregate(value=Sum("amount_minor"))["value"] or 0

    def amount(minor):
        return Decimal(minor) / Decimal(100)

    def formatted(minor):
        return f"{amount(minor):,.2f} {currency}"

    change = (
        (Decimal(total_minor - previous_minor) * 100 / previous_minor).quantize(
            Decimal(".1"), rounding=ROUND_HALF_UP
        )
        if previous_minor
        else Decimal(0)
    )
    properties = []
    for row in (
        current.values(
            "transaction__lease__property__id", "transaction__lease__property__title"
        )
        .annotate(total=Sum("amount_minor"))
        .order_by("transaction__lease__property__id")
    ):
        properties.append(
            {
                "id": str(row["transaction__lease__property__id"]),
                "title": row["transaction__lease__property__title"],
                "amount": amount(row["total"]),
                "formatted_amount": formatted(row["total"]),
                "currency": currency,
                "status": "paid",
                "status_label": "تم التحويل" if arabic else "Transferred",
                "status_color": "green",
                "due_date": None,
            }
        )
    transactions = []
    for row in entries.select_related("transaction__lease__property").order_by(
        "-transaction__created_at", "-pk"
    )[:20]:
        transaction = row.transaction
        day = timezone.localtime(transaction.created_at, cairo).date().isoformat()
        transactions.append(
            {
                "id": str(transaction.id),
                "title": transaction.lease.property.title,
                "date": day,
                "date_iso": day,
                "amount": amount(row.amount_minor),
                "formatted_amount": "+" + formatted(row.amount_minor),
                "currency": currency,
                "type": "credit",
                "is_credit": True,
            }
        )
    return {
        "total_this_month": amount(total_minor),
        "formatted_total": formatted(total_minor),
        "currency": currency,
        "percentage_change": change,
        "comparison_text": f"{basis} ({change:+.1f}%)" if previous_minor else basis,
        "is_positive": total_minor >= previous_minor,
        "properties": properties,
        "recent_transactions": transactions,
    }
