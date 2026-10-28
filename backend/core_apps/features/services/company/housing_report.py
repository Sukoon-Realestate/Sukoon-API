"""Management statement over canonical records; no new financial ledger."""

import csv
import io
from datetime import date
from uuid import UUID
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from . import rental_summary, tenancy_access
from .access import member_for
from ..rental_phase3 import invoice_balance_minor


def filters(params):
    result = {
        k: params.get(k, "").strip()
        for k in ("project_code", "cost_center", "tenancy_id", "from", "until")
    }
    if any(len(result[k]) > 100 for k in ("project_code", "cost_center")):
        raise ValidationError(
            "Use project and cost-center codes of at most 100 characters."
        )
    try:
        if result["tenancy_id"]:
            UUID(result["tenancy_id"])
        for key in ("from", "until"):
            result[key] = date.fromisoformat(result[key]) if result[key] else None
    except (ValueError, TypeError):
        raise ValidationError("Use an exact tenancy ID and civil ISO dates.")
    if result["from"] and result["until"] and result["until"] <= result["from"]:
        raise ValidationError("The exclusive end must follow the start.")
    return result


def _date_matches(value, values):
    return (
        value is not None
        and (not values["from"] or value >= values["from"])
        and (not values["until"] or value < values["until"])
    )


def _overlaps(start, end, values):
    return (not values["from"] or end > values["from"]) and (
        not values["until"] or start < values["until"]
    )


def _request_matches(requirement, values):
    return all(
        not values[k] or getattr(requirement, k) == values[k]
        for k in ("project_code", "cost_center")
    )


def payload(user, company, params):
    values = filters(params)
    member = member_for(user, company)
    rows = []

    def add(kind, record, requirement, *, tenancy=None, **fields):
        rows.append(
            {
                "kind": kind,
                "id": str(record.id),
                "tenancy_id": str(tenancy.id) if tenancy else "",
                "request_id": str(requirement.id),
                "title": requirement.title,
                "project_code": requirement.project_code,
                "cost_center": requirement.cost_center,
                "currency": "EGP",
                "exponent": 2,
                "amount_minor": None,
                "balance_minor": None,
                "state": "",
                "reference": "",
                "date": "",
                "basis": "",
                **fields,
            }
        )

    # Budget reservations are exposure, not invoices/payments. Only uncontracted
    # packages appear here; the same package cannot be counted as a contract too.
    budgets = company.budget_reservations.filter(
        status="reserved", item__lease__isnull=True
    ).select_related("item__request")
    from .listing_changes import live_budget

    budgets = live_budget(budgets)
    from .role_context import selected

    role = selected(user, company)
    if role is not None:
        # The payment report contains only this delegate's canonical tenancies.
        # Other memberships never add uncontracted approval-budget records.
        budgets = budgets.none()
    elif not (member.is_admin or member.is_approver):
        budgets = (
            budgets.filter(item__request__coordinator=user)
            if member.is_coordinator
            else budgets.none()
        )
    if not values["tenancy_id"]:
        for reservation in budgets:
            requirement = reservation.item.request
            if _request_matches(requirement, values) and _overlaps(
                requirement.starts_on, requirement.ends_on_exclusive, values
            ):
                add(
                    "reserved_rent",
                    reservation,
                    requirement,
                    amount_minor=reservation.rent_minor,
                    state=reservation.status,
                    basis="full_uncontracted_package_exposure",
                )
                add(
                    "reserved_deposit",
                    reservation,
                    requirement,
                    amount_minor=reservation.deposit_minor,
                    state=reservation.status,
                    basis="separate_deposit_exposure",
                )

    for item in rental_summary.tenancies(user, company):
        if not (tenancy_access.roles(item, user) - tenancy_access.PRIVATE_ONLY):
            continue
        requirement, lease = item.preparation.booking.request, item.lease
        if values["tenancy_id"] and str(item.id) != values["tenancy_id"]:
            continue
        if not _request_matches(requirement, values):
            continue
        # Period-level rows retain changes/renewals and avoid prorating partial
        # months or multiplying today's price across historical periods.
        if lease.status in {"signed", "active", "termination_pending", "ended"}:
            for period in lease.billing_periods.exclude(status="cancelled").order_by(
                "sequence"
            ):
                if _overlaps(period.start, period.end_exclusive, values):
                    add(
                        "contract_rent",
                        period,
                        requirement,
                        tenancy=item,
                        amount_minor=period.amount_minor,
                        state=period.status,
                        date=str(period.start),
                        basis="whole_billing_period_overlapping_filter",
                        ends_on_exclusive=str(period.end_exclusive),
                    )
        for invoice in lease.invoices.order_by("due_date", "id"):
            if not _date_matches(invoice.due_date, values):
                continue
            add(
                "invoice",
                invoice,
                requirement,
                tenancy=item,
                amount_minor=invoice.charges_minor,
                balance_minor=invoice_balance_minor(invoice),
                credits_minor=invoice.credits_minor,
                applied_minor=invoice.applied_minor,
                state=invoice.status,
                reference=invoice.reference,
                date=str(invoice.due_date),
                basis="invoice_due_date_in_range",
                invoice_type=invoice.invoice_type,
                collectible=invoice.status
                not in {"cancelled", "written_off", "settled"},
            )
        from ...models import PaymentAttempt

        for payment in PaymentAttempt.objects.filter(
            invoice__lease=lease, payment_status__in=["captured", "chargedback"]
        ).select_related("invoice"):
            when = (
                timezone.localdate(payment.confirmed_at)
                if payment.confirmed_at
                else None
            )
            if not _date_matches(when, values):
                continue
            add(
                "payment",
                payment,
                requirement,
                tenancy=item,
                amount_minor=payment.amount_minor,
                state=payment.payment_status,
                reference=str(payment.invoice.id),
                date=str(when),
                basis="gross_capture_confirmation_date_not_invoice_payment_total",
                allocated_minor=getattr(
                    getattr(payment, "invoice_allocation", None), "amount_minor", None
                ),
                provider_mode=(
                    "mock"
                    if payment.provider_attempt_id.startswith("mock-")
                    else "integration_unverified"
                ),
            )
        for payment in lease.rental_changes.filter(
            kind="external_payment", status="applied"
        ):
            when = (
                timezone.localdate(payment.applied_at) if payment.applied_at else None
            )
            if _date_matches(when, values):
                add(
                    "external_payment",
                    payment,
                    requirement,
                    tenancy=item,
                    amount_minor=payment.amount_minor,
                    state=payment.status,
                    reference=str(payment.invoice.id) if payment.invoice_id else "",
                    date=str(when),
                    basis="applied_external_payment_date",
                )
        if _overlaps(lease.start_date, lease.end_date, values):
            deposit = getattr(lease, "deposit_agreement", None)
            add(
                "deposit",
                deposit or lease,
                requirement,
                tenancy=item,
                amount_minor=deposit.agreed_minor if deposit else None,
                collected_minor=deposit.collected_minor if deposit else None,
                returned_minor=deposit.returned_minor if deposit else None,
                applied_minor=deposit.applied_minor if deposit else None,
                disputed_minor=deposit.disputed_minor if deposit else None,
                holder=lease.terms.get("deposit_holder"),
                basis="current_custody_snapshot_not_period_income",
                state="recorded" if deposit else "not_established",
            )
    totals = {}
    for kind in sorted({r["kind"] for r in rows}):
        selected = [r for r in rows if r["kind"] == kind]
        amounts = [r["amount_minor"] for r in selected]
        totals[kind] = {
            "amount_minor": (
                sum(amounts) if all(v is not None for v in amounts) else None
            ),
            "records": len(selected),
        }
    return {
        "company_id": str(company.id),
        "checked_at": timezone.now().isoformat(),
        "currency": "EGP",
        "exponent": 2,
        "filters": {k: str(v) if v is not None else None for k, v in values.items()},
        "rows": rows,
        "totals": totals,
        "basis": "Separate record categories overlap economically. Never sum categories. This is a management statement, not a tax invoice, payment instruction or account balance.",
    }


def csv_bytes(report):
    fields = [
        "kind",
        "id",
        "tenancy_id",
        "request_id",
        "title",
        "project_code",
        "cost_center",
        "currency",
        "exponent",
        "amount_minor",
        "balance_minor",
        "credits_minor",
        "applied_minor",
        "collected_minor",
        "returned_minor",
        "disputed_minor",
        "allocated_minor",
        "holder",
        "state",
        "reference",
        "date",
        "ends_on_exclusive",
        "basis",
        "invoice_type",
        "collectible",
        "provider_mode",
    ]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in report["rows"]:
        writer.writerow(
            {
                key: (
                    "'" + value
                    if isinstance(value, str)
                    and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r"))
                    else value
                )
                for key, value in row.items()
            }
        )
    return ("\ufeff" + stream.getvalue()).encode("utf-8")
