"""Public aggregates deliberately exclude private review bodies and party identities."""

from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q, Exists, OuterRef
from rest_framework.exceptions import NotFound
from .visibility import sections, published, summarize_rows
from .policy import CRITERIA
from ...models import (
    RentInvoice,
    RentalOperationalCase,
    RentalDispute,
    Company,
    RefundRequest,
    PaymentAttempt,
)
from ..rent_payment_reminders import effective_due


def payment_reliability(kind, identity, *, now=None):
    now = now or timezone.now()
    if kind not in {"person_tenant", "organization_renter"}:
        return None
    party = (
        {"lease__tenant__id": identity, "lease__renter_company__isnull": True}
        if kind == "person_tenant"
        else {"lease__renter_company__id": identity}
    )
    invoices = (
        RentInvoice.objects.filter(
            Q(due_at__gte=now - timedelta(days=365))
            | Q(deferred_until__gte=now - timedelta(days=365)),
            **party,
            purpose="rent",
            invoice_type="rent",
            due_at__isnull=False,
        )
        .exclude(status__in=["scheduled", "cancelled", "written_off"])
        .annotate(
            uncertain_payment=Exists(
                PaymentAttempt.objects.filter(
                    invoice_id=OuterRef("pk"),
                    payment_status__in=[
                        "created",
                        "pending",
                        "authorized",
                        "chargedback",
                    ],
                )
            ),
            financial_case=Exists(
                RentalOperationalCase.objects.filter(
                    Q(payment_attempt__invoice_id=OuterRef("pk"))
                    | Q(refund__payment_attempt__invoice_id=OuterRef("pk"))
                ).exclude(status="resolved")
            ),
            disputed=Exists(
                RentalDispute.objects.filter(
                    lease_id=OuterRef("lease_id"),
                    subject_kind="invoice",
                    subject_id=OuterRef("id"),
                    status="open",
                )
            ),
            refunded_or_pending=Exists(
                RefundRequest.objects.filter(
                    payment_attempt__invoice_id=OuterRef("pk"),
                    status__in=["requested", "approved", "processing", "succeeded"],
                )
            ),
        )
        .prefetch_related("payment_allocations__payment_attempt")
    )
    eligible = on_time = late = unpaid = excluded = 0
    for invoice in invoices.iterator(chunk_size=250):
        due = effective_due(invoice)
        if not due or due > now or due < now - timedelta(days=365):
            continue
        if (
            invoice.uncertain_payment
            or invoice.financial_case
            or invoice.disputed
            or invoice.refunded_or_pending
        ):
            excluded += 1
            continue
        obligation = (
            invoice.amount_minor + invoice.charges_minor - invoice.credits_minor
        )
        if obligation <= 0:
            continue
        allocations = sorted(
            [
                row
                for row in invoice.payment_allocations.all()
                if row.payment_attempt.payment_status == "captured"
                and row.payment_attempt.confirmed_at
            ],
            key=lambda row: row.payment_attempt.confirmed_at,
        )
        total = 0
        satisfied = None
        for row in allocations:
            total += row.amount_minor
            if total >= obligation:
                satisfied = row.payment_attempt.confirmed_at
                break
        if invoice.status in {"paid", "settled"} and satisfied is None:
            excluded += 1
            continue
        eligible += 1
        if satisfied is not None and satisfied <= due:
            on_time += 1
        else:
            late += 1
            if satisfied is None:
                unpaid += 1
    return {
        "window_months": 12,
        "sample_count": eligible,
        "on_time_percentage": (
            round(100 * on_time / eligible, 1) if eligible >= 3 else None
        ),
        "late_count": late if eligible >= 3 else None,
        "overdue_unpaid_count": unpaid if eligible >= 3 else None,
        "limited_sample": eligible < 3,
        "excluded_count": excluded,
        "computed_at": now.isoformat(),
    }


def public_summary(kind, identity):
    if kind not in CRITERIA or kind.startswith("property_"):
        raise NotFound()
    model = Company if kind.startswith("organization_") else get_user_model()
    filters = {"id": identity}
    if model is not Company:
        filters["is_active"] = True
    if not model.objects.filter(**filters).exists():
        raise NotFound()
    # Publication/release and authoritative source checks still apply to private
    # sections. Only their aggregate becomes public; detail authorization stays.
    rows = [
        row
        for row in sections().filter(
            subject_kind=kind, subject_id=identity, content_state="approved"
        )
        if published(row) and row.verification_basis != "legacy_unverified"
    ]
    result = summarize_rows(kind, rows)
    if result["distinct_experience_count"] < 3:
        result.update(average=None, distribution={}, criteria={}, limited_sample=True)
    result["payment_reliability"] = payment_reliability(kind, identity)
    return result
