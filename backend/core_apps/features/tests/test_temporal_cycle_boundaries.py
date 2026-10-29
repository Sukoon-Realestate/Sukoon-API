"""Civil-time and invoice boundaries for isolated pytest records.

Only for an isolated pytest database. Invokes existing tasks synchronously under
one patched clock: no deployed worker/runtime-clock or provider evidence.
"""

from datetime import date, datetime, time, timedelta, timezone as dt_timezone
from importlib import import_module

import pytest
from django.utils import timezone

from core_apps.features.models import BillingPeriod, LedgerTransaction, RentalTimelineEvent
from core_apps.features.services.legal_lifecycle import end_lease_if_due
from core_apps.features.services.rental_phase3_parts.issue_invoice import cairo_instant
from core_apps.features.tasks import run_rental_billing_cycle
from .test_rental_phase5 import phase5_lease


@pytest.mark.django_db
def test_billing_issue_is_inclusive_and_overdue_is_strict_after_cairo_due_time(
    phase5_lease, monkeypatch,
):
    _, _, lease = phase5_lease
    # A scheduled monthly period inside this fresh fixture's original term.
    start, end = date(2026, 11, 1), date(2026, 12, 1)
    issue_at = (cairo_instant(start) - timedelta(days=7)).astimezone(dt_timezone.utc)
    due_at = cairo_instant(start, time.max).astimezone(dt_timezone.utc)
    period = BillingPeriod.objects.create(
        lease=lease, sequence=11, start=start, end_exclusive=end,
        issue_at=issue_at, due_at=due_at, amount_minor=1000, status="scheduled",
    )
    clock = {"now": issue_at - timedelta(microseconds=1)}
    monkeypatch.setattr(timezone, "now", lambda: clock["now"])

    with timezone.override("Africa/Cairo"):
        assert run_rental_billing_cycle() == {"issued": 0, "overdue": 0}
        assert not lease.invoices.exists()
        clock["now"] = issue_at
        assert run_rental_billing_cycle() == {"issued": 1, "overdue": 0}
        invoice = lease.invoices.get(billing_period=period)
        original_revision = invoice.revision
        assert invoice.status == "due" and invoice.amount_minor == 1000
        clock["now"] = issue_at + timedelta(microseconds=1)
        assert run_rental_billing_cycle() == {"issued": 0, "overdue": 0}
        clock["now"] = due_at
        assert run_rental_billing_cycle() == {"issued": 0, "overdue": 0}
        clock["now"] = due_at + timedelta(microseconds=1)
        assert run_rental_billing_cycle() == {"issued": 0, "overdue": 1}
        assert run_rental_billing_cycle() == {"issued": 0, "overdue": 0}

    period.refresh_from_db()
    invoice.refresh_from_db()
    assert period.status == "issued"
    assert invoice.revision == original_revision + 1 and invoice.status == "overdue"
    assert lease.invoices.count() == 1
    assert LedgerTransaction.objects.filter(reference=f"invoice-issued:{invoice.id}").count() == 1


@pytest.mark.django_db
def test_natural_end_uses_exclusive_cairo_day_even_in_utc_request_context(
    phase5_lease, monkeypatch,
):
    _, _, lease = phase5_lease
    original_end = lease.end_date
    boundary = cairo_instant(original_end).astimezone(dt_timezone.utc)
    clock = {"now": boundary - timedelta(microseconds=1)}
    monkeypatch.setattr(timezone, "now", lambda: clock["now"])

    with timezone.override("UTC"):
        assert end_lease_if_due(lease) is False
        lease.refresh_from_db()
        assert lease.status == "active" and lease.occupancy_status == "occupied"
        clock["now"] = boundary
        assert end_lease_if_due(lease) is True
        lease.refresh_from_db()
        ended_revision = lease.revision
        assert lease.status == "ended" and lease.occupancy_status == "move_out_pending"
        assert lease.financial_closure_status == "open"
        clock["now"] = boundary + timedelta(microseconds=1)
        assert end_lease_if_due(lease) is False

    lease.refresh_from_db()
    assert lease.end_date == original_end and lease.revision == ended_revision
    assert RentalTimelineEvent.objects.filter(lease=lease, kind="legally_ended").count() == 1


@pytest.mark.parametrize("civil_day, expected_utc, fold", [
    (date(2026, 10, 29), "2026-10-29T21:59:59.999999+00:00", 1),
    (date(2026, 10, 28), "2026-10-28T20:59:59.999999+00:00", 0),
    (date(2026, 10, 30), "2026-10-30T21:59:59.999999+00:00", 0),
    (date(2026, 4, 23), "2026-04-23T21:59:59.999999+00:00", 0),
    (date(2026, 4, 24), "2026-04-24T20:59:59.999999+00:00", 0),
])
def test_cairo_day_end_is_the_final_instant_before_the_next_civil_day(
    civil_day, expected_utc, fold,
):
    deadline = cairo_instant(civil_day, time.max)
    utc = deadline.astimezone(dt_timezone.utc)
    assert utc.isoformat() == expected_utc
    assert deadline.date() == civil_day and deadline.fold == fold
    assert (utc + timedelta(microseconds=1)).astimezone(deadline.tzinfo).date() == civil_day + timedelta(days=1)
    assert utc.astimezone(deadline.tzinfo) == deadline
    if fold:
        repeated_hour = datetime(2026, 10, 29, 21, 30, tzinfo=dt_timezone.utc)
        assert deadline > repeated_hour
        assert deadline.replace(fold=0).astimezone(dt_timezone.utc) < repeated_hour


@pytest.mark.django_db
def test_preexisting_invoice_deadline_is_not_recomputed_after_cairo_fold_fix(
    phase5_lease, monkeypatch,
):
    _, _, lease = phase5_lease
    billing = import_module("core_apps.features.services.rental_phase3_parts.issue_invoice")
    start, end = date(2026, 10, 29), date(2026, 11, 29)
    activation = datetime(2026, 10, 29, 20, 30, tzinfo=dt_timezone.utc)
    lease.start_date, lease.end_date, lease.activated_at = start, end, activation
    lease.terms = {**lease.terms, "starts_on": str(start), "ends_on_exclusive": str(end),
                   "handover_on": str(start), "billing_anchor_day": start.day}
    lease.save()
    # Synthetic prior state uses the old renderer of a civil end, never live data.
    with monkeypatch.context() as previous:
        previous.setattr(billing, "cairo_instant", lambda day, at_time=time.min:
                         datetime.combine(day, at_time, tzinfo=billing.CAIRO))
        billing.generate_billing_schedule(lease)
    invoice = lease.invoices.get()
    original_id, original_due, original_revision = invoice.id, invoice.due_at, invoice.revision
    assert original_due.isoformat() == "2026-10-29T20:59:59.999999+00:00"
    assert original_due != cairo_instant(start, time.max).astimezone(dt_timezone.utc)

    billing.generate_billing_schedule(lease)
    invoice.refresh_from_db()
    assert invoice.id == original_id and invoice.due_at == original_due
    assert invoice.revision == original_revision
    assert lease.billing_periods.get().due_at == original_due
    assert lease.invoices.count() == 1
