"""Financial projections from posted EGP ledger entries, never asking prices."""

import logging
from decimal import Decimal
from django.db.models import Avg, Sum
from django.utils import timezone
from core_apps.features.models import LedgerEntry, Lease, PaymentAttempt
from core_apps.features.services.rental_phase2 import add_months

logger = logging.getLogger(__name__)


def money(value):
    return f"{Decimal(value) / 100:,.2f} EGP" if value is not None else "Unavailable"


def net(entries):
    credits = (
        entries.filter(direction="credit").aggregate(value=Sum("amount_minor"))["value"]
        or 0
    )
    debits = (
        entries.filter(direction="debit").aggregate(value=Sum("amount_minor"))["value"]
        or 0
    )
    return credits - debits


def get_financial_summary():
    now = timezone.localtime()
    month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    entries = LedgerEntry.objects.filter(currency="EGP", exponent=2)
    current = entries.filter(transaction__occurred_at__gte=month)
    values = {
        "platformFees": net(current.filter(account="commission_revenue")),
        "subscriptions": net(
            current.filter(
                account="purchase_revenue", transaction__invoice__purpose="subscription"
            )
        ),
        "advertising": net(
            current.filter(
                account="purchase_revenue", transaction__invoice__purpose="advertising"
            )
        ),
    }
    total = sum(values.values())
    trend = []
    for offset in range(-5, 1):
        start = add_months(month.date(), offset)
        end = add_months(month.date(), offset + 1)
        posted = entries.filter(
            transaction__occurred_at__date__gte=start,
            transaction__occurred_at__date__lt=end,
            account__in=["commission_revenue", "purchase_revenue"],
        )
        trend.append(
            {
                "month": start.strftime("%Y-%m"),
                "value": net(posted) / 100,
                "isCurrent": offset == 0,
            }
        )
    average = Lease.objects.filter(status="active", rent_currency="EGP").aggregate(
        value=Avg("rent_amount_minor")
    )["value"]
    return {
        "metrics": {
            "avgRent": money(average),
            "activeTransactions": str(
                PaymentAttempt.objects.filter(
                    payment_status__in=["created", "pending", "authorized"]
                ).count()
            ),
            "platformFees": money(values["platformFees"]),
            "totalRevenueMonth": money(total),
        },
        "revenueBreakdown": {
            name: {
                "value": money(value),
                "percent": max(0, min(100, value * 100 / total)) if total > 0 else 0,
            }
            for name, value in values.items()
        },
        "sixMonthTrend": trend,
        "basis": "Posted EGP ledger revenue, net of recorded reversals; deposits, rent liabilities and unearned commission are excluded. Provider settlement and unposted external events are not inferred.",
    }
