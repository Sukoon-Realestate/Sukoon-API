"""Civil-day reminders and current responsibility; FCM is simulated explicitly."""

import json
import uuid
from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import patch
import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.exceptions import NotFound
from core_apps.features.models import (
    BillingPeriod,
    PrivateAccessRevocation,
    RentInvoice,
)
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.rent_payment_reminders import (
    CAIRO,
    EVENT_KINDS,
    authorize,
    record_reminders,
    record_invoice,
)
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.features.services.rental_phase3_parts.issue_invoice import issue_invoice
from core_apps.notifications.models import DeviceToken, Notification, PushDelivery
from core_apps.notifications.services.push_delivery import dispatch
from core_apps.notifications.services.fcm_service import FCMService
from .test_rental_phase5 import phase5_lease
from .test_company_tenancy import (
    signed_agreement,
    agreement,
    cycle,
    company_setup,
    rental_participants,
    policy,
)

pytestmark = pytest.mark.django_db
NOW = datetime(2026, 10, 20, 9, tzinfo=CAIRO)


@pytest.fixture
def invoice(phase5_lease):
    _, _, lease = phase5_lease
    due = datetime(2026, 10, 23, 23, 59, 59, tzinfo=CAIRO)
    return RentInvoice.objects.create(
        lease=lease,
        reference="REMINDER",
        due_date=due.date(),
        due_at=due,
        charges_minor=10000,
        amount_minor=10000,
        status="due",
    )


def test_three_civil_days_at_nine_dry_run_and_deduplication(invoice):
    assert record_reminders(now=NOW - timedelta(microseconds=1)) == {"created": 0}
    before = (invoice.revision, invoice.applied_minor, invoice.status)
    result = record_reminders(now=NOW, dry_run=True)
    assert result["created"] == 0 and len(result["candidates"]) == 1
    assert not PlanningEvent.objects.exists()
    assert record_reminders(now=NOW) == {"created": 1}
    invoice.revision += 1
    invoice.applied_minor = 500
    invoice.status = "partially_paid"
    invoice.save()
    assert record_reminders(now=NOW + timedelta(days=1)) == {"created": 0}
    event = PlanningEvent.objects.get()
    assert event.recipient == invoice.lease.tenant
    assert event.destination["event_kind"] == "rent_payment_reminder"
    assert event.destination["invoice_id"] == str(invoice.id)
    assert "amount" not in event.destination and "address" not in event.destination
    assert before == (1, 0, "due")
    invoice.refresh_from_db()
    assert (invoice.revision, invoice.applied_minor, invoice.status) == (
        2,
        500,
        "partially_paid",
    )


@pytest.mark.parametrize(
    "due",
    [
        datetime(2026, 11, 1, 23, 59, tzinfo=CAIRO),  # crosses Cairo DST boundary
        datetime(2027, 3, 1, 23, 59, tzinfo=CAIRO),  # crosses February
        datetime(2027, 1, 1, 23, 59, tzinfo=CAIRO),
    ],
)
def test_calendar_boundary_is_cairo_civil_time(invoice, due):
    invoice.due_at = due
    invoice.save()
    threshold = datetime.combine(
        due.date() - timedelta(days=3),
        datetime.min.time().replace(hour=9),
        tzinfo=CAIRO,
    )
    assert record_reminders(now=threshold - timedelta(microseconds=1))["created"] == 0
    assert (
        record_reminders(now=threshold.astimezone(timezone.get_default_timezone()))[
            "created"
        ]
        == 1
    )


@pytest.mark.parametrize(
    "change",
    [
        {"status": "paid"},
        {"status": "cancelled"},
        {"applied_minor": 10000},
        {"credits_minor": 10000},
        {"due_at": NOW},
        {"due_at": None},
    ],
)
def test_non_payable_invoice_has_no_reminder(invoice, change):
    RentInvoice.objects.filter(pk=invoice.pk).update(**change)
    assert record_reminders(now=NOW)["created"] == 0


@pytest.mark.parametrize(
    "state,legacy,hold",
    [
        ("draft", False, None),
        ("cancelled", False, None),
        ("active", True, None),
        ("signed", False, NOW),
    ],
)
def test_invalid_lease_or_expired_hold_has_no_reminder(invoice, state, legacy, hold):
    lease = invoice.lease
    lease.status, lease.legacy_read_only, lease.hold_expires_at = state, legacy, hold
    lease.save()
    assert record_reminders(now=NOW)["created"] == 0


def test_approved_extension_invalidates_old_event_and_creates_one_for_new_due(invoice):
    record_reminders(now=NOW)
    old = PlanningEvent.objects.get()
    invoice.deferred_until = invoice.due_at + timedelta(days=7)
    invoice.save()
    with patch("django.utils.timezone.now", return_value=NOW):
        with pytest.raises(NotFound):
            authorize(old)
    assert record_reminders(now=NOW)["created"] == 0
    assert record_reminders(now=NOW + timedelta(days=7))["created"] == 1
    assert record_reminders(now=NOW + timedelta(days=8))["created"] == 0


def test_worker_catches_up_only_before_due_and_rechecks_paid_before_dispatch(
    invoice, monkeypatch
):
    assert record_reminders(now=invoice.due_at - timedelta(seconds=1))["created"] == 1
    invoice.status, invoice.applied_minor = "paid", invoice.charges_minor
    invoice.save()
    monkeypatch.setattr(
        FCMService, "send_push_to_user", lambda **kw: pytest.fail("No stale push")
    )
    with patch("django.utils.timezone.now", return_value=NOW):
        assert deliver_planning_events(event_kinds=EVENT_KINDS) == 0
    assert PlanningEvent.objects.get().delivery_status == "stale_or_unauthorized"
    assert not Notification.objects.exists()
    assert record_reminders(now=invoice.due_at + timedelta(seconds=1))["created"] == 0


def test_first_invoice_outbox_is_created_in_issuance_transaction(phase5_lease):
    _, tenant, lease = phase5_lease
    lease.status, lease.hold_expires_at = "signed", NOW + timedelta(hours=48)
    lease.save()
    period = BillingPeriod.objects.create(
        lease=lease,
        sequence=1,
        start=NOW.date(),
        end_exclusive=(NOW + timedelta(days=31)).date(),
        issue_at=NOW,
        due_at=lease.hold_expires_at,
        amount_minor=10000,
    )
    with patch("django.utils.timezone.now", return_value=NOW):
        made = issue_invoice(period)
        assert issue_invoice(period).pk == made.pk
    event = PlanningEvent.objects.get(recipient=tenant)
    assert event.destination["event_kind"] == "rent_initial_payment_due"
    assert record_reminders(now=NOW)["created"] == 0


def test_revocation_and_retries_preserve_one_inbox_notification(invoice, monkeypatch):
    record_reminders(now=NOW)
    DeviceToken.objects.create(user=invoice.lease.tenant, token="synthetic-device")
    monkeypatch.setattr(FCMService, "send_push_to_device", lambda **kw: False)
    with patch("django.utils.timezone.now", return_value=NOW):
        assert deliver_planning_events(event_kinds=EVENT_KINDS) == 1
        PushDelivery.objects.update(next_attempt_at=NOW)
        assert dispatch() == 0
    event = PlanningEvent.objects.get()
    assert event.attempts == 1 and event.delivery_status == "push_queued"
    assert not event.provider_accepted_at and PushDelivery.objects.get().attempts == 1
    assert Notification.objects.count() == 1
    PrivateAccessRevocation.objects.create(
        lease=invoice.lease, user=invoice.lease.tenant, reason="Authority withdrawn"
    )
    with patch("django.utils.timezone.now", return_value=NOW + timedelta(minutes=3)):
        assert deliver_planning_events(event_kinds=EVENT_KINDS) == 0
        assert dispatch() == 0
    event.refresh_from_db()
    assert not event.provider_accepted_at and PushDelivery.objects.get().suppressed
    assert Notification.objects.count() == 1


def test_successful_retry_and_repeat_job_do_not_duplicate_notification(
    invoice, monkeypatch
):
    record_reminders(now=NOW)
    DeviceToken.objects.create(user=invoice.lease.tenant, token="synthetic-device")
    calls = []
    monkeypatch.setattr(
        FCMService, "send_push_to_device", lambda **kw: calls.append(kw) or True
    )
    with patch("django.utils.timezone.now", return_value=NOW):
        assert deliver_planning_events(event_kinds=EVENT_KINDS) == 1
        assert deliver_planning_events(event_kinds=EVENT_KINDS) == 0
        PushDelivery.objects.update(next_attempt_at=NOW)
        assert dispatch() == 1
        assert dispatch() == 0
    assert len(calls) == Notification.objects.count() == 1
    assert PlanningEvent.objects.get().provider_accepted_at


def test_company_payer_coordinator_only_and_current_membership(signed_agreement):
    people, item = signed_agreement
    invoice = item.lease.invoices.get()
    events = PlanningEvent.objects.filter(destination__event_kind__in=EVENT_KINDS)
    assert set(events.values_list("recipient_id", flat=True)) == {
        people["payer"].pk,
        people["coordinator"].pk,
    }
    assert not events.filter(recipient=people["employee"]).exists()
    payer_event = events.get(recipient=people["payer"])
    membership = item.payer_mandate.membership
    membership.is_active = False
    membership.save()
    with pytest.raises(NotFound):
        authorize(payer_event)
    coordinator_event = events.get(recipient=people["coordinator"])
    _, role = authorize(coordinator_event)
    assert role == "authority_required"
    assert record_invoice(invoice) == 0


def test_command_is_read_only_by_default(invoice):
    output = StringIO()
    with patch("django.utils.timezone.now", return_value=NOW):
        call_command("rent_payment_notifications", stdout=output)
    assert len(json.loads(output.getvalue())["candidates"]) == 1
    assert not PlanningEvent.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_generators_share_one_canonical_event(invoice):
    from django.db import connection
    from .test_cycle_concurrency import parallel_calls

    if connection.vendor != "postgresql":
        pytest.skip("Real row-lock verification requires PostgreSQL")
    results = parallel_calls(lambda _: record_reminders(now=NOW))
    assert sum(row["created"] for row in results) == 1
    assert PlanningEvent.objects.count() == 1


def test_same_deadline_in_another_timezone_is_the_same_event(invoice):
    assert record_invoice(invoice, now=NOW) == 1
    invoice.refresh_from_db()
    assert record_invoice(invoice, now=NOW) == 0
    assert PlanningEvent.objects.count() == 1


def test_beat_names_resolve_to_registered_payment_tasks(settings):
    from config.celery import app
    from core_apps.features.tasks import (
        process_rent_payment_notifications,
        run_rental_billing_cycle,
    )

    for schedule, task in [
        ("rent-payment-notifications", process_rent_payment_notifications),
        ("run-rental-billing-cycle", run_rental_billing_cycle),
    ]:
        name = settings.CELERY_BEAT_SCHEDULE[schedule]["task"]
        assert name == task.name
        assert app.tasks[name] is task._get_current_object()


def test_pending_attempt_reminder_instructs_original_operation_recovery(invoice):
    from core_apps.features.models import PaymentAttempt, PaymentQuote
    from core_apps.features.services.rent_payment_reminders import notification_copy

    quote = PaymentQuote.objects.create(
        invoice=invoice,
        request_key=uuid.uuid4(),
        invoice_revision=1,
        payer_amount_minor=10000,
        policy_version="test",
        fingerprint="synthetic",
        expires_at=NOW + timedelta(hours=1),
    )
    PaymentAttempt.objects.create(
        invoice=invoice,
        payer=invoice.lease.tenant,
        quote=quote,
        request_key=uuid.uuid4(),
        invoice_revision=1,
        amount_minor=10000,
        policy_version="test",
        quote_fingerprint="synthetic",
        payment_status="pending",
    )
    record_reminders(now=NOW)
    with patch("django.utils.timezone.now", return_value=NOW):
        assert (
            "original payment" in notification_copy(PlanningEvent.objects.get())["body"]
        )
    assert invoice.payment_attempts.count() == 1


def test_company_role_overlap_is_one_reminder(signed_agreement):
    from core_apps.features.services.rent_payment_recipients import recipients

    people, item = signed_agreement
    item.coordinator = people["payer"]
    item.save()
    member = item.payer_mandate.membership
    member.is_coordinator = True
    member.save()
    invoice = RentInvoice.objects.get(lease=item.lease)
    assert recipients(invoice) == [(people["payer"], "payer")]
