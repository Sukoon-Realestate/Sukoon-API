import json
import uuid
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from core_apps.features.models import (
    InvoicePaymentAllocation,
    PaymentAttempt,
    RentalOperationalCase,
    RentalProviderInstruction,
)
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.rental_lifecycle.cases import open_system_case
from core_apps.features.tests.test_rental_lifecycle_safety import checkout
from core_apps.features.tests.test_rental_phase3 import phase3_lease

pytestmark = pytest.mark.django_db


def observe():
    stream = StringIO()
    with CaptureQueriesContext(connection) as queries:
        call_command("rental_closure_status", stdout=stream)
    assert queries
    assert all(item["sql"].lstrip().upper().startswith("SELECT") for item in queries)
    return json.loads(stream.getvalue()), stream.getvalue()


def test_empty_closure_snapshot_is_read_only_and_does_not_claim_success():
    result, _ = observe()
    assert result["schema_version"] == 2
    assert result["frozen_sensitive_accounts"] == 0
    assert result["policy_decisions_missing"] == [
        f"D{number:02}" for number in range(1, 34)
    ]
    assert all(
        value == {"count": 0, "oldest_created_at": None, "oldest_age_seconds": None}
        for value in result["queues"].values()
    )


def test_closure_snapshot_tracks_original_queues_without_exposing_private_records(
    phase3_lease,
):
    _, tenant, lease = phase3_lease
    attempt = checkout(tenant, lease)
    item = open_system_case(
        kind="payment_unknown",
        source_key="closure-metrics-private-case",
        lease=lease,
        actor=tenant,
        reason="Sensitive private evidence",
        next_action="Review original attempt",
    )
    old = timezone.now() - timedelta(hours=2)
    RentalOperationalCase.objects.filter(pk=item.pk).update(due_at=old, created_at=old)
    instruction = RentalProviderInstruction.objects.create(
        reference="private-provider-instruction",
        kind="refund",
        provider="fake",
        subject_id=uuid.uuid4(),
        subject_revision=1,
        status="unknown",
        request_fingerprint="a" * 64,
        provider_reference="private-provider-reference",
    )
    existing_events = PlanningEvent.objects.filter(delivered_at__isnull=True).count()
    event = PlanningEvent.objects.create(
        recipient=tenant,
        event_key="private-outbox-key",
        destination={"kind": "open_support_ticket", "id": str(uuid.uuid4())},
    )
    result, output = observe()
    queues = result["queues"]
    for key in (
        "pending_rent_payments",
        "unresolved_provider_instructions",
        "unresolved_cases",
        "overdue_cases",
        "unassigned_cases",
    ):
        assert queues[key]["count"] == 1, key
    assert queues["undelivered_planning_events"]["count"] == existing_events + 1
    assert queues["overdue_cases"]["oldest_age_seconds"] >= 7200
    assert queues["captured_rent_payments_without_allocation"]["count"] == 0
    for private in (
        str(tenant.id),
        str(attempt.id),
        str(item.id),
        str(attempt.request_key),
        "Sensitive private evidence",
        "private-provider-reference",
        "private-outbox-key",
    ):
        assert private not in output

    # Fixture transitions model observed canonical states, not actual provider execution.
    PaymentAttempt.objects.filter(pk=attempt.pk).update(payment_status="captured")
    RentalOperationalCase.objects.filter(pk=item.pk).update(status="resolved")
    RentalProviderInstruction.objects.filter(pk=instruction.pk).update(
        status="confirmed"
    )
    PlanningEvent.objects.filter(pk=event.pk).update(delivered_at=timezone.now())
    result, _ = observe()
    queues = result["queues"]
    assert queues["captured_rent_payments_without_allocation"]["count"] == 1
    assert all(
        queues[key]["count"] == 0
        for key in (
            "pending_rent_payments",
            "unresolved_provider_instructions",
            "unresolved_cases",
            "overdue_cases",
            "unassigned_cases",
        )
    )
    assert queues["undelivered_planning_events"]["count"] == existing_events
    InvoicePaymentAllocation.objects.create(
        invoice=attempt.invoice,
        payment_attempt=attempt,
        amount_minor=attempt.amount_minor,
    )
    result, _ = observe()
    assert result["queues"]["captured_rent_payments_without_allocation"]["count"] == 0
