import hashlib
import hmac
import json

import pytest
from django.test import Client
from django.urls import reverse

from .paymob_models import PaymobCallbackEvent

SECRET = "callback-test-secret"
TRANSACTION = {
    "amount_cents": 10000,
    "created_at": "2026-10-18T20:00:00",
    "currency": "EGP",
    "error_occured": False,
    "has_parent_transaction": False,
    "id": 123,
    "integration_id": 5991528,
    "is_3d_secure": True,
    "is_auth": False,
    "is_capture": False,
    "is_refunded": False,
    "is_standalone_payment": True,
    "is_voided": False,
    "order": {"id": 456},
    "owner": 789,
    "pending": False,
    "source_data": {"pan": "2346", "sub_type": "MasterCard", "type": "card"},
    "success": True,
}


def signature(obj):
    # Independent signing fixture: don't call the implementation under test.
    values = [
        obj["amount_cents"],
        obj["created_at"],
        obj["currency"],
        obj["error_occured"],
        obj["has_parent_transaction"],
        obj["id"],
        obj["integration_id"],
        obj["is_3d_secure"],
        obj["is_auth"],
        obj["is_capture"],
        obj["is_refunded"],
        obj["is_standalone_payment"],
        obj["is_voided"],
        obj["order"]["id"],
        obj["owner"],
        obj["pending"],
        obj["source_data"]["pan"],
        obj["source_data"]["sub_type"],
        obj["source_data"]["type"],
        obj["success"],
    ]
    message = "".join(str(v).lower() if isinstance(v, bool) else str(v) for v in values)
    return hmac.new(SECRET.encode(), message.encode(), hashlib.sha512).hexdigest()


@pytest.fixture(autouse=True)
def paymob_config(settings):
    settings.PAYMOB_HMAC_SECRET = SECRET
    settings.PAYMOB_INTEGRATION_ID = "5991528"


def send(client, obj=None, signed=None):
    obj = TRANSACTION if obj is None else obj
    return client.post(
        reverse("paymob-webhook") + "?hmac=" + (signed or signature(obj)),
        data=json.dumps({"type": "TRANSACTION", "obj": obj}),
        content_type="application/json",
    )


@pytest.mark.django_db
def test_webhook_is_public_csrf_exempt_durable_and_idempotent():
    client = Client(enforce_csrf_checks=True)
    assert send(client).json() == {"received": True, "duplicate": False}
    assert send(client).json() == {"received": True, "duplicate": True}
    event = PaymobCallbackEvent.objects.get()
    assert event.transaction_id == "123"
    assert event.order_id == "456"
    assert event.reported_status == "succeeded"
    assert event.amount_cents == 10000
    assert "2346" not in json.dumps(event.flags)


@pytest.mark.django_db
@pytest.mark.parametrize("change", [{"amount_cents": 1}, {"success": False}])
def test_tampered_notifications_are_not_stored(client, change):
    assert (
        send(client, {**TRANSACTION, **change}, signature(TRANSACTION)).status_code
        == 403
    )
    assert not PaymobCallbackEvent.objects.exists()


@pytest.mark.django_db
def test_separate_transaction_states_remain_separate_events(client):
    assert send(client).status_code == 200
    assert send(client, {**TRANSACTION, "pending": True}).status_code == 200
    assert PaymobCallbackEvent.objects.count() == 2
    assert set(
        PaymobCallbackEvent.objects.values_list("reported_status", flat=True)
    ) == {"pending", "succeeded"}


@pytest.mark.django_db
def test_wrong_integration_rejected_even_with_valid_signature(client):
    assert send(client, {**TRANSACTION, "integration_id": 999}).status_code == 403
    assert not PaymobCallbackEvent.objects.exists()


@pytest.mark.parametrize(
    "body",
    ["not-json", "[]", "{}", '{"type":"TOKEN"}', '{"type":"TRANSACTION","obj":null}'],
)
def test_malformed_callbacks(client, body):
    assert (
        client.post(
            reverse("paymob-webhook") + "?hmac=bad",
            data=body,
            content_type="application/json",
        ).status_code
        == 400
    )


def test_configuration_and_method_checks(client, settings):
    settings.PAYMOB_HMAC_SECRET = ""
    assert send(client).status_code == 503
    assert client.get(reverse("paymob-webhook")).status_code == 405
    assert client.post(reverse("paymob-return")).status_code == 405
    assert (
        client.post(
            reverse("paymob-webhook"), data="x", content_type="text/plain"
        ).status_code
        == 415
    )


def query(obj):
    result = {
        key: str(value).lower() if isinstance(value, bool) else value
        for key, value in obj.items()
        if key not in {"order", "source_data"}
    }
    result["order"] = obj["order"]["id"]
    result.update(
        {"source_data." + key: value for key, value in obj["source_data"].items()}
    )
    result["hmac"] = signature(obj)
    return result


@pytest.mark.django_db
@pytest.mark.parametrize(
    "changes,status",
    [
        ({}, "succeeded"),
        ({"pending": True}, "pending"),
        ({"success": False}, "failed"),
        ({"is_refunded": True}, "refunded"),
        ({"is_voided": True}, "voided"),
        ({"is_auth": True}, "authorized"),
    ],
)
def test_return_displays_signed_outcome_without_writing_payment_state(
    client, changes, status
):
    response = client.get(reverse("paymob-return"), query({**TRANSACTION, **changes}))
    assert response.status_code == 200
    assert ("<strong>" + status + "</strong>").encode() in response.content
    assert "no-store" in response["Cache-Control"]
    assert response["Referrer-Policy"] == "no-referrer"
    assert not PaymobCallbackEvent.objects.exists()


def test_unsigned_or_tampered_return_rejected(client):
    assert client.get(reverse("paymob-return")).status_code == 403
    params = query(TRANSACTION)
    params["success"] = "false"
    assert client.get(reverse("paymob-return"), params).status_code == 403
    params["hmac"] = "é" * 128
    assert client.get(reverse("paymob-return"), params).status_code == 403


def test_duplicate_query_fields_rejected(client):
    assert (
        client.get(reverse("paymob-return") + "?success=true&success=false").status_code
        == 400
    )
