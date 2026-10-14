"""Revenue is confirmed money movement, never listing prices or customer charges."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse

from core_apps.features.models import Lease, LedgerTransaction
from core_apps.features.services.rental_phase3 import post_ledger_transaction
from .test_rental_phase2 import authenticated, rental_participants


@pytest.mark.django_db
def test_owner_revenue_uses_payout_ledger_and_cairo_month(
    rental_participants, monkeypatch
):
    owner, tenant, stranger, prop, _ = rental_participants
    cairo = ZoneInfo("Africa/Cairo")
    now = datetime(2026, 2, 15, 12, tzinfo=cairo)
    boundary = datetime(2026, 2, 1, tzinfo=cairo)
    monkeypatch.setattr(
        "core_apps.properties.services.owner_revenues.timezone.now", lambda: now
    )
    lease = Lease.objects.create(
        owner=owner,
        tenant=tenant,
        property=prop,
        template_id="local",
        template_version="1",
        start_date=now.date(),
        end_date=now.date() + timedelta(days=30),
        rent_amount_minor=500000,
    )

    def post(reference, value, at, kind="owner_payout"):
        transaction = post_ledger_transaction(
            reference=reference,
            kind=kind,
            lease=lease,
            entries=[
                ("owner_liability", "debit", value),
                ("platform_cash", "credit", value),
            ],
        )
        LedgerTransaction.objects.filter(pk=transaction.pk).update(created_at=at)
        return transaction

    current = post("payout:current", 125025, boundary)
    post("payout:previous", 50000, boundary - timedelta(seconds=1))
    post("capture:is-not-owner-income", 900000, now, kind="payment_allocated")
    response = authenticated(owner).get(
        reverse("owner-revenues"), HTTP_ACCEPT_LANGUAGE="en"
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_this_month"] == 1250.25
    assert data["percentage_change"] == 150.1
    assert data["comparison_text"] == "Confirmed owner payouts (+150.1%)"
    assert len(data["properties"]) == 1
    assert data["properties"][0]["id"] == str(prop.id)
    assert data["properties"][0]["status"] == "paid"
    assert data["properties"][0]["amount"] == 1250.25
    assert data["recent_transactions"][0]["id"] == str(current.id)
    assert len(data["recent_transactions"]) == 2
    # An unrelated authenticated account sees neither the total nor history.
    hidden = authenticated(stranger).get(reverse("owner-revenues")).json()["data"]
    assert hidden["total_this_month"] == 0
    assert hidden["properties"] == hidden["recent_transactions"] == []
