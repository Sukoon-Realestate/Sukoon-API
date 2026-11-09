"""A4-02: personal private-access revocation applies to financial reads and new commands.

Policy implemented in Sprint 01 (pending product sign-off): a personal lease participant
with a PrivateAccessRevocation loses general invoice/payment list, detail, quote, checkout
and resume access (same rule company roles already follow). The original payer can still
reconcile their own earlier attempt. Server-side provider reconciliation is not user-gated.
"""

import uuid

import pytest

from core_apps.features.models import PaymentAttempt, PrivateAccessRevocation
from core_apps.features.services.company.tenancy_access import can_pay, financial_read
from core_apps.features.services.rental_phase3 import generate_billing_schedule
from core_apps.features.tests.test_rental_phase3 import client_for, phase3_lease  # noqa: F401

pytestmark = [pytest.mark.django_db, pytest.mark.mvp_deferred]
BASE = "/api/v1/features/v1"


def _checkout(client, invoice):
    quote = client.post(
        f"{BASE}/rent-invoices/{invoice.id}/quote/",
        {"action": "quote", "expected_revision": invoice.revision, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert quote.status_code == 201, quote.data
    checkout = client.post(
        f"{BASE}/rent-invoices/{invoice.id}/checkout/",
        {
            "invoice_id": str(invoice.id),
            "quote_id": quote.data["resource"]["quote_id"],
            "expected_revision": invoice.revision,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert checkout.status_code == 201, checkout.data
    return checkout.data["resource"]["payment_attempt_id"]


def _revoke(lease, user):
    PrivateAccessRevocation.objects.create(lease=lease, user=user, reason="Explicit restriction")


def test_helpers_honor_personal_revocation(phase3_lease):  # noqa: F811
    owner, tenant, lease = phase3_lease
    assert financial_read(lease, tenant) and can_pay(lease, tenant)
    _revoke(lease, tenant)
    assert not financial_read(lease, tenant)
    assert not can_pay(lease, tenant)
    assert financial_read(lease, owner), "revoking one participant leaves the other unaffected"


def test_revoked_tenant_loses_detail_list_and_new_commands(phase3_lease):  # noqa: F811
    owner, tenant, lease = phase3_lease
    invoice = list(generate_billing_schedule(lease))[0].invoice
    client = client_for(tenant)
    attempt_id = _checkout(client, invoice)
    _revoke(lease, tenant)

    assert client.get(f"{BASE}/rent-invoices/{invoice.id}/payments/").status_code == 404
    assert client.get(f"{BASE}/payment-attempts/{attempt_id}/").status_code == 404
    quote = client.post(
        f"{BASE}/rent-invoices/{invoice.id}/quote/",
        {"action": "quote", "expected_revision": invoice.revision, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert quote.status_code == 404


def test_original_payer_can_still_reconcile_their_own_attempt(phase3_lease):  # noqa: F811
    owner, tenant, lease = phase3_lease
    invoice = list(generate_billing_schedule(lease))[0].invoice
    client = client_for(tenant)
    attempt_id = _checkout(client, invoice)
    _revoke(lease, tenant)
    attempt = PaymentAttempt.objects.get(id=attempt_id)

    response = client.post(
        f"{BASE}/payment-attempts/{attempt_id}/reconcile/",
        {"action": "reconcile", "expected_revision": attempt.revision},
        format="json",
    )
    assert response.status_code == 200, response.data


def test_owner_keeps_access_when_only_the_tenant_is_revoked(phase3_lease):  # noqa: F811
    owner, tenant, lease = phase3_lease
    invoice = list(generate_billing_schedule(lease))[0].invoice
    _checkout(client_for(tenant), invoice)
    _revoke(lease, tenant)
    assert client_for(owner).get(f"{BASE}/rent-invoices/{invoice.id}/payments/").status_code == 200


def test_billing_invoice_list_drops_revoked_lease_rent(phase3_lease):  # noqa: F811
    from core_apps.features.services.billing_invoices import invoice_queryset

    owner, tenant, lease = phase3_lease
    invoice = list(generate_billing_schedule(lease))[0].invoice
    assert invoice in invoice_queryset(tenant, "tenant")
    _revoke(lease, tenant)
    assert invoice not in invoice_queryset(tenant, "tenant")
