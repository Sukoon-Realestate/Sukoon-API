import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from rest_framework.test import APIClient

from core_apps.features.models import (
    Lease,
    LedgerEntry,
    OwnerPayable,
    PaymentAttempt,
    ProviderWebhookEvent,
)
from core_apps.features.providers import sign_fake_webhook
from core_apps.features.services.rental_phase3 import generate_billing_schedule
from core_apps.properties.models import City, Governorate, Property, PropertyType
from core_apps.users.models import User


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def phase3_lease(db):
    owner = User.objects.create_user(
        email="p3-owner@example.com", password="pass", is_verified=True
    )
    tenant = User.objects.create_user(
        email="p3-tenant@example.com", password="pass", is_verified=True
    )
    governorate = Governorate.objects.create(name="P3 Cairo")
    city = City.objects.create(name="P3 City", governorate=governorate)
    property_type = PropertyType.objects.create(
        name="P3 Apartment", slug="p3-apartment"
    )
    property_obj = Property.objects.create(
        owner=owner,
        title="P3 Home",
        price=10000,
        property_type=property_type,
        governorate=governorate,
        city=city,
        district="District",
        status=Property.Status.VERIFIED,
        is_verified=True,
        is_ownership_verified=True,
    )
    lease = Lease.objects.create(
        property=property_obj,
        owner=owner,
        tenant=tenant,
        template_id="eg-v1",
        template_version="1",
        start_date=date(2024, 1, 31),
        end_date=date(2024, 4, 30),
        rent_amount_minor=1_000_000,
        status=Lease.Status.ACTIVE,
        legacy_read_only=False,
        offer_id=str(uuid.uuid4()),
        terms={"handover_on": "2024-01-31"},
        activated_at=datetime(2024, 1, 29, 12, tzinfo=ZoneInfo("Africa/Cairo")),
    )
    return owner, tenant, lease


@pytest.mark.django_db
def test_billing_anchor_preserves_month_end_and_issues_first_invoice(phase3_lease):
    _, _, lease = phase3_lease
    periods = list(generate_billing_schedule(lease))

    assert [(p.start, p.end_exclusive) for p in periods] == [
        (date(2024, 1, 31), date(2024, 2, 29)),
        (date(2024, 2, 29), date(2024, 3, 31)),
        (date(2024, 3, 31), date(2024, 4, 30)),
    ]
    assert periods[0].invoice.lines.get().amount_minor == 1_000_000
    assert periods[0].invoice.charges_minor == 1_000_000


@pytest.mark.django_db
def test_quote_checkout_recovery_and_out_of_order_webhooks(phase3_lease):
    owner, tenant, lease = phase3_lease
    invoice = list(generate_billing_schedule(lease))[0].invoice
    client = client_for(tenant)
    quote_key = uuid.uuid4()
    quote_response = client.post(
        f"/api/v1/features/v1/rent-invoices/{invoice.id}/quote/",
        {
            "action": "quote",
            "expected_revision": invoice.revision,
            "request_key": str(quote_key),
        },
        format="json",
    )
    assert quote_response.status_code == 201
    quote = quote_response.data["resource"]
    assert quote["tenant_service_fee"]["amount_minor"] == 0

    checkout_key = uuid.uuid4()
    body = {
        "invoice_id": str(invoice.id),
        "quote_id": quote["quote_id"],
        "expected_revision": invoice.revision,
        "request_key": str(checkout_key),
    }
    checkout = client.post(
        f"/api/v1/features/v1/rent-invoices/{invoice.id}/checkout/", body, format="json"
    )
    assert checkout.status_code == 201
    resource = checkout.data["resource"]
    attempt_id = resource["payment_attempt_id"]
    assert resource["navigation"]["allowed_origins"] == [
        "https://fake-rental-provider.test"
    ]

    replay = client.post(
        f"/api/v1/features/v1/rent-invoices/{invoice.id}/checkout/", body, format="json"
    )
    assert replay.status_code == 201
    assert replay.data == checkout.data
    recovery = client.get(
        f"/api/v1/features/v1/payment-attempts/?invoice_id={invoice.id}&request_key={checkout_key}"
    )
    assert recovery.data["absence_confirmed"] is False
    assert recovery.data["active_session"]["session_id"] == resource["session_id"]

    webhook = APIClient()
    settled = {
        "event_id": "evt-settle",
        "type": "payment.settled",
        "sequence": 2,
        "payment_attempt_id": attempt_id,
        "amount_minor": 1_000_000,
        "currency": "EGP",
    }
    assert (
        webhook.post(
            "/api/v1/features/v1/provider-webhooks/payments/",
            settled,
            format="json",
            HTTP_X_RENTAL_SIGNATURE=sign_fake_webhook(settled),
        ).status_code
        == 200
    )
    assert (
        ProviderWebhookEvent.objects.get(provider_event_id="evt-settle").processed
        is False
    )

    captured = {
        "event_id": "evt-capture",
        "type": "payment.captured",
        "sequence": 1,
        "payment_attempt_id": attempt_id,
        "amount_minor": 1_000_000,
        "currency": "EGP",
    }
    assert (
        webhook.post(
            "/api/v1/features/v1/provider-webhooks/payments/",
            captured,
            format="json",
            HTTP_X_RENTAL_SIGNATURE=sign_fake_webhook(captured),
        ).status_code
        == 200
    )
    attempt = PaymentAttempt.objects.get(id=attempt_id)
    assert attempt.payment_status == PaymentAttempt.Status.CAPTURED
    assert attempt.settlement_status == "settled"
    payable = OwnerPayable.objects.get(payment_attempt=attempt)
    assert payable.commission_minor == 100_000
    assert payable.net_minor == 900_000
    assert (
        client_for(owner)
        .get("/api/v1/features/v1/owner-payables/?workspace=owner")
        .status_code
        == 200
    )
    for ledger_transaction in attempt.ledger_transactions.all():
        debits = sum(
            x.amount_minor
            for x in ledger_transaction.entries.filter(
                direction=LedgerEntry.Direction.DEBIT
            )
        )
        credits = sum(
            x.amount_minor
            for x in ledger_transaction.entries.filter(
                direction=LedgerEntry.Direction.CREDIT
            )
        )
        assert debits == credits

    duplicate = webhook.post(
        "/api/v1/features/v1/provider-webhooks/payments/",
        captured,
        format="json",
        HTTP_X_RENTAL_SIGNATURE=sign_fake_webhook(captured),
    )
    assert duplicate.status_code == 200
    assert duplicate.data["duplicate"] is True


@pytest.mark.django_db
def test_checkout_return_data_never_captures_payment(phase3_lease):
    _, tenant, lease = phase3_lease
    invoice = list(generate_billing_schedule(lease))[0].invoice
    response = client_for(tenant).get(
        f"/api/v1/features/v1/rent-invoices/{invoice.id}/?success=true"
    )
    assert response.status_code == 200
    assert not PaymentAttempt.objects.filter(
        payment_status=PaymentAttempt.Status.CAPTURED
    ).exists()
