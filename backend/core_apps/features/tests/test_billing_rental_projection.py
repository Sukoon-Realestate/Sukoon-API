"""My Invoices preserves historical rent and agreed settlement credits."""

import uuid
from datetime import date
from types import SimpleNamespace

import pytest

from core_apps.features.models import RentInvoice
from core_apps.features.services.rental_phase3 import generate_billing_schedule
from core_apps.features.services.settlements_parts.apply_credit import _apply_credit
from core_apps.features.tests.test_billing_subscriptions import ROOT, body
from core_apps.features.tests.test_rental_phase3 import client_for, phase3_lease

pytestmark = pytest.mark.django_db


def test_historical_rent_without_lines_preserves_recorded_amount(phase3_lease):
    owner, tenant, lease = phase3_lease
    invoice = RentInvoice.objects.create(
        lease=lease,
        reference="HISTORICAL-UNITEMIZED",
        due_date=date(2026, 1, 1),
        amount_minor=12500,
        status="due",
    )
    client = client_for(tenant)
    path = ROOT + f"billing/invoices/{invoice.id}/"
    detail = body(client.get(path))
    listed = body(client.get(ROOT + "billing/invoices/", {"workspace": "tenant"}))
    assert listed == [detail]
    assert detail["total_minor"] == detail["balance_minor"] == 12500
    assert detail["paid_minor"] == 0 and detail["lines"] == []
    assert body(client_for(owner).get(path), 404) is None
    invoice.refresh_from_db()
    assert invoice.amount_minor == 12500 and invoice.charges_minor == 0
    assert not invoice.lines.exists() and not invoice.payment_attempts.exists()


def test_settlement_credit_reduces_obligation_without_inventing_payment(phase3_lease):
    _, tenant, lease = phase3_lease
    invoice = list(generate_billing_schedule(lease))[0].invoice
    invoice.applied_minor = 300000
    invoice.status = "partially_paid"
    invoice.save(update_fields=["applied_minor", "status"])
    _apply_credit(
        lease,
        SimpleNamespace(id=uuid.uuid4()),
        {
            "invoice_id": str(invoice.id),
            "amount_minor": 200000,
            "type": "credit",
            "line_id": "agreed-credit",
        },
        0,
    )
    client = client_for(tenant)
    detail = body(client.get(ROOT + f"billing/invoices/{invoice.id}/"))
    listed = body(client.get(ROOT + "billing/invoices/", {"workspace": "tenant"}))
    assert listed == [detail]
    assert detail["total_minor"] == 800000
    assert detail["paid_minor"] == 300000
    assert detail["balance_minor"] == 500000
    assert sorted(line["amount_minor"] for line in detail["lines"]) == [
        -200000,
        1000000,
    ]
    invoice.refresh_from_db()
    assert invoice.amount_minor == invoice.charges_minor == 1000000
    assert invoice.credits_minor == 200000 and invoice.applied_minor == 300000
