from io import StringIO

import pytest
from django.core.management import call_command

from core_apps.features.models import Lease, RentInvoice
from .test_rental_phase4 import phase4_lease


@pytest.mark.django_db
def test_closure_repair_is_explicit_idempotent_and_preserves_obligations(phase4_lease):
    _, _, lease = phase4_lease
    lease.status = Lease.Status.CANCELLED
    lease.save()
    original_revision = lease.revision
    call_command("reconcile_cancelled_rental_closure", stdout=StringIO())
    lease.refresh_from_db()
    assert lease.financial_closure_status == "open"
    assert lease.revision == original_revision
    invoice = RentInvoice.objects.create(
        lease=lease,
        reference="REPAIR-BLOCKED",
        due_date=lease.start_date,
        amount_minor=1000,
        charges_minor=1000,
    )
    call_command("reconcile_cancelled_rental_closure", apply=True, stdout=StringIO())
    lease.refresh_from_db()
    assert lease.financial_closure_status == "open"
    invoice.status = RentInvoice.Status.CANCELLED
    invoice.save()
    call_command("reconcile_cancelled_rental_closure", apply=True, stdout=StringIO())
    lease.refresh_from_db()
    assert lease.financial_closure_status == "closed"
    assert lease.revision == original_revision + 1
    call_command("reconcile_cancelled_rental_closure", apply=True, stdout=StringIO())
    lease.refresh_from_db()
    assert lease.revision == original_revision + 1
    invoice.refresh_from_db()
    assert invoice.charges_minor == 1000
