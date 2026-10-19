"""Invoice reads must not replace the authoritative billing lifecycle."""

from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.features.models import RentInvoice
from core_apps.features.tasks import run_rental_billing_cycle
from core_apps.users.models import User
from .test_rental_phase3 import phase3_lease  # noqa: F401


def overdue_candidate(lease, *, deferred=False, reference="read-recovery"):
    due_at = timezone.now() - timedelta(days=2)
    return RentInvoice.objects.create(
        lease=lease,
        reference=reference,
        due_date=due_at.date(),
        due_at=due_at,
        deferred_until=timezone.now() + timedelta(days=2) if deferred else None,
        amount_minor=10000,
        charges_minor=10000,
        status=RentInvoice.Status.DUE,
        revision=7,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("actor", ["tenant", "owner", "unrelated", "invalid_workspace"])
def test_invoice_list_never_changes_status_or_an_approved_extension(
    phase3_lease, actor
):
    owner, tenant, lease = phase3_lease
    invoice = overdue_candidate(lease, deferred=True)
    user = owner if actor == "owner" else tenant
    if actor == "unrelated":
        user = User.objects.create_user(email="invoice-outsider@example.invalid")
    client = APIClient()
    client.force_authenticate(user)
    workspace = "owner" if actor == "owner" else "tenant"
    if actor == "invalid_workspace":
        workspace = "invalid"
    response = client.get(
        "/api/v1/features/v1/rent-invoices/", {"workspace": workspace}
    )
    assert response.status_code == (400 if actor == "invalid_workspace" else 200)
    invoice.refresh_from_db()
    assert invoice.status == RentInvoice.Status.DUE
    assert invoice.revision == 7


@pytest.mark.django_db
def test_invoice_list_performs_only_reads_even_for_past_due_dates(phase3_lease):
    _, tenant, lease = phase3_lease
    invoice = overdue_candidate(lease)
    client = APIClient()
    client.force_authenticate(tenant)
    with CaptureQueriesContext(connection) as queries:
        response = client.get(
            "/api/v1/features/v1/rent-invoices/", {"workspace": "tenant"}
        )
    assert response.status_code == 200
    assert not any(
        query["sql"].lstrip().upper().startswith(("UPDATE", "INSERT", "DELETE"))
        for query in queries
    )
    invoice.refresh_from_db()
    assert invoice.status == RentInvoice.Status.DUE


@pytest.mark.django_db
def test_billing_worker_owns_overdue_transition_and_respects_extension(phase3_lease):
    _, _, lease = phase3_lease
    due = overdue_candidate(lease)
    deferred = overdue_candidate(
        lease, deferred=True, reference="read-recovery-deferred"
    )
    first = run_rental_billing_cycle.run()
    second = run_rental_billing_cycle.run()
    due.refresh_from_db()
    deferred.refresh_from_db()
    assert first == {"issued": 0, "overdue": 1}
    assert second == {"issued": 0, "overdue": 0}
    assert (due.status, due.revision) == (RentInvoice.Status.OVERDUE, 8)
    assert (deferred.status, deferred.revision) == (RentInvoice.Status.DUE, 7)
