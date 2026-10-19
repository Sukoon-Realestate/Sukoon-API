"""A missing checkout is unknown until its original key is durably closed."""

import uuid

import pytest
from django.db import connection

from core_apps.features.models import IdempotencyRecord, PaymentAttempt
from core_apps.features.services.rental_phase3 import generate_billing_schedule
from core_apps.features.tests.test_rental_phase3 import client_for, phase3_lease
from core_apps.features.tests.test_cycle_concurrency import parallel_calls


pytestmark = pytest.mark.django_db
LOOKUP = "/api/v1/features/v1/payment-attempts/"


def prepared(phase3_lease):
    owner, payer, lease = phase3_lease
    invoice = list(generate_billing_schedule(lease))[0].invoice
    client = client_for(payer)
    response = client.post(
        f"/api/v1/features/v1/rent-invoices/{invoice.id}/quote/",
        {
            "action": "quote",
            "expected_revision": invoice.revision,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert response.status_code == 201
    body = {
        "invoice_id": str(invoice.id),
        "quote_id": response.data["resource"]["quote_id"],
        "expected_revision": invoice.revision,
        "request_key": str(uuid.uuid4()),
    }
    return owner, payer, invoice, client, body


def recovery_body(body):
    return {
        "invoice_id": body["invoice_id"],
        "request_key": body["request_key"],
        "action": "resolve_checkout",
    }


def checkout(client, body):
    return client.post(
        f"/api/v1/features/v1/rent-invoices/{body['invoice_id']}/checkout/",
        body,
        format="json",
    )


def test_read_absence_does_not_claim_a_late_checkout_is_impossible(phase3_lease):
    _, _, invoice, client, body = prepared(phase3_lease)
    lookup = client.get(LOOKUP, recovery_body(body))
    assert lookup.status_code == 200 and lookup.data["results"] == []
    late = checkout(client, body)
    assert late.status_code == 201
    assert PaymentAttempt.objects.filter(invoice=invoice).count() == 1
    assert lookup.data["absence_confirmed"] is False


def test_explicit_recovery_closes_original_key_but_not_a_fresh_intention(phase3_lease):
    _, payer, invoice, client, body = prepared(phase3_lease)
    recovered = client.post(LOOKUP, recovery_body(body), format="json")
    assert recovered.status_code == 200
    assert recovered.data["absence_confirmed"] is True
    assert client.get(LOOKUP, recovery_body(body)).data["absence_confirmed"] is True
    late = checkout(client, body)
    assert late.status_code == 409
    assert PaymentAttempt.objects.filter(invoice=invoice).count() == 0
    receipt = IdempotencyRecord.objects.get(
        user=payer,
        operation=f"invoice.checkout.{invoice.id}",
        request_key=body["request_key"],
    )
    assert receipt.recovery_status == "absent_final"
    again = client.post(LOOKUP, recovery_body(body), format="json")
    assert again.status_code == 200 and again.data == recovered.data
    assert (
        checkout(client, {**body, "request_key": str(uuid.uuid4())}).status_code == 201
    )


def test_recovery_of_acknowledged_checkout_retains_original_session(phase3_lease):
    _, _, invoice, client, body = prepared(phase3_lease)
    created = checkout(client, body)
    assert created.status_code == 201
    recovered = client.post(LOOKUP, recovery_body(body), format="json")
    assert recovered.status_code == 200
    assert recovered.data["absence_confirmed"] is False
    assert (
        recovered.data["active_session"]["session_id"]
        == created.data["resource"]["session_id"]
    )
    assert PaymentAttempt.objects.filter(invoice=invoice).count() == 1
    assert checkout(client, body).data == created.data


def test_owner_cannot_close_a_payer_operation(phase3_lease):
    owner, _, invoice, _, body = prepared(phase3_lease)
    response = client_for(owner).post(LOOKUP, recovery_body(body), format="json")
    assert response.status_code == 403
    assert not IdempotencyRecord.objects.filter(
        operation=f"invoice.checkout.{invoice.id}", request_key=body["request_key"]
    ).exists()


def test_recovery_and_read_remain_available_with_checkout_disabled(
    phase3_lease, settings
):
    _, _, invoice, client, body = prepared(phase3_lease)
    settings.RENTAL_CHECKOUT_ENABLED = False
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = False
    capabilities = client.get(
        "/api/v1/features/v1/rental-capabilities/",
        {"subject_id": str(invoice.id), "action": "resolve_checkout"},
    )
    assert capabilities.status_code == 200
    assert "resolve_checkout" in capabilities.data["allowed_actions"]
    assert "checkout" not in capabilities.data["allowed_actions"]
    response = client.post(LOOKUP, recovery_body(body), format="json")
    assert response.status_code == 200 and response.data["absence_confirmed"] is True
    assert "no-store" in response["Cache-Control"]
    assert not PaymentAttempt.objects.filter(invoice=invoice).exists()


@pytest.mark.parametrize(
    "payload",
    [
        {"action": "resolve_checkout", "invoice_id": "bad", "request_key": "bad"},
        {
            "action": "replay",
            "invoice_id": str(uuid.uuid4()),
            "request_key": str(uuid.uuid4()),
        },
    ],
)
def test_recovery_validates_command_without_server_error(phase3_lease, payload):
    _, payer, _ = phase3_lease
    assert client_for(payer).post(LOOKUP, payload, format="json").status_code == 400


@pytest.mark.django_db(transaction=True)
def test_checkout_racing_its_closure_has_one_durable_outcome(phase3_lease):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock race requires PostgreSQL")
    _, payer, invoice, _, body = prepared(phase3_lease)

    def call(index):
        client = client_for(payer)
        return (
            checkout(client, body)
            if index
            else client.post(LOOKUP, recovery_body(body), format="json")
        )

    resolved, created = parallel_calls(call)
    assert resolved.status_code == 200
    if resolved.data["absence_confirmed"]:
        assert created.status_code == 409
        assert not PaymentAttempt.objects.filter(invoice=invoice).exists()
    else:
        assert created.status_code == 201
        assert (
            resolved.data["results"][0]["id"]
            == created.data["resource"]["payment_attempt_id"]
        )
        assert PaymentAttempt.objects.filter(invoice=invoice).count() == 1
    assert (
        IdempotencyRecord.objects.filter(
            user=payer,
            operation=f"invoice.checkout.{invoice.id}",
            request_key=body["request_key"],
        ).count()
        == 1
    )


@pytest.mark.django_db(transaction=True)
def test_concurrent_closures_share_one_tombstone(phase3_lease):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock race requires PostgreSQL")
    _, payer, invoice, _, body = prepared(phase3_lease)
    responses = parallel_calls(
        lambda _: client_for(payer).post(LOOKUP, recovery_body(body), format="json")
    )
    assert [r.status_code for r in responses] == [200, 200]
    assert responses[0].data == responses[1].data
    assert responses[0].data["absence_confirmed"] is True
    assert (
        IdempotencyRecord.objects.filter(
            user=payer,
            operation=f"invoice.checkout.{invoice.id}",
            request_key=body["request_key"],
        ).count()
        == 1
    )
