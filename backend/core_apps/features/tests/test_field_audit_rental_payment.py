import uuid

import pytest

from core_apps.features.models import PaymentAttempt, PaymentQuote
from core_apps.features.services.rental_phase3 import generate_billing_schedule
from core_apps.features.tests.test_rental_phase3 import phase3_lease, client_for

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("extra", [{}, {"decision": "", "note": ""}])
def test_minimal_and_legacy_quote_bodies_preserve_exact_replay(phase3_lease, extra):
    _, tenant, lease = phase3_lease
    invoice = list(generate_billing_schedule(lease))[0].invoice
    client = client_for(tenant)
    path = f"/api/v1/features/v1/rent-invoices/{invoice.id}/quote/"
    body = {
        "expected_revision": invoice.revision,
        "request_key": str(uuid.uuid4()),
        **extra,
    }
    first = client.post(path, body, format="json")
    assert first.status_code == 201
    assert client.post(path, body, format="json").json() == first.json()
    resource = first.json()["data"]["resource"]
    assert resource["invoice_id"] == str(invoice.id)
    assert resource["payer_amount"]["amount_minor"] == invoice.amount_minor
    changed = {**body, "note": "Different fingerprint"}
    assert client.post(path, changed, format="json").status_code == 409
    assert PaymentQuote.objects.filter(invoice=invoice).count() == 1


def test_minimal_reconcile_remains_a_payer_only_status_read(phase3_lease):
    owner, tenant, lease = phase3_lease
    invoice = list(generate_billing_schedule(lease))[0].invoice
    client = client_for(tenant)
    quote = client.post(
        f"/api/v1/features/v1/rent-invoices/{invoice.id}/quote/",
        {
            "expected_revision": invoice.revision,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    ).json()["data"]["resource"]
    attempt = PaymentAttempt.objects.create(
        invoice=invoice,
        payer=tenant,
        quote=PaymentQuote.objects.get(id=quote["quote_id"]),
        request_key=uuid.uuid4(),
        invoice_revision=invoice.revision,
        amount_minor=invoice.amount_minor,
        policy_version=quote["policy_version"],
        quote_fingerprint=quote["fingerprint"],
    )
    path = f"/api/v1/features/v1/payment-attempts/{attempt.id}/reconcile/"
    body = {
        "decision": "reconcile",
        "expected_revision": attempt.revision,
        "request_key": str(uuid.uuid4()),
    }
    first = client.post(path, body, format="json")
    assert first.status_code == 200
    assert first.json()["data"]["request_key"] == str(attempt.request_key)
    assert client.post(path, body, format="json").json() == first.json()
    assert client_for(owner).post(path, body, format="json").status_code == 403
    assert (
        client.post(path, {**body, "expected_revision": 99}, format="json").status_code
        == 409
    )
    attempt.refresh_from_db()
    assert attempt.revision == 1 and attempt.payment_status == "created"
