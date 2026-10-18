import io
import json
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse

import pytest
from django.test import Client
from django.urls import reverse


@pytest.fixture(autouse=True)
def checkout_config(settings):
    settings.PAYMOB_TEST_CHECKOUT_ENABLED = True
    settings.PAYMOB_SECRET_KEY = "egy_sk_test_synthetic"
    settings.PAYMOB_PUBLIC_KEY = "egy_pk_test_synthetic"
    settings.PAYMOB_INTEGRATION_ID = "5991528"
    settings.PAYMOB_HMAC_SECRET = "synthetic-hmac"
    settings.PAYMOB_WEBHOOK_URL = (
        "https://api.sukoon.rent/api/v1/payments/paymob/webhook/"
    )
    settings.PAYMOB_RETURN_URL = (
        "https://api.sukoon.rent/api/v1/payments/paymob/return/"
    )


def details(**changes):
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone_number": "+201012345678",
        "language": "en",
        **changes,
    }


def provider_response():
    return io.BytesIO(b'{"client_secret":"sandbox-client-secret"}')


def test_native_landing_form_opens_fixed_price_test_checkout_without_csrf():
    client = Client(enforce_csrf_checks=True)
    with patch(
        "core_apps.common.paymob_checkout.urlopen", return_value=provider_response()
    ) as call:
        response = client.post(
            reverse("paymob-test-checkout"),
            details(
                amount=1,
                currency="USD",
                payment_methods="999",
                notification_url="https://attacker.test",
            ),
        )
    assert response.status_code == 303
    request = call.call_args.args[0]
    payload = json.loads(request.data)
    assert request.full_url == "https://accept.paymob.com/v1/intention/"
    assert request.get_header("Authorization") == "Token egy_sk_test_synthetic"
    assert call.call_args.kwargs["timeout"] == 15
    assert payload["amount"] == 1000
    assert payload["currency"] == "EGP"
    assert payload["payment_methods"] == [5991528]
    assert (
        payload["notification_url"]
        == "https://api.sukoon.rent/api/v1/payments/paymob/webhook/"
    )
    assert (
        payload["redirection_url"]
        == "https://api.sukoon.rent/api/v1/payments/paymob/return/"
    )
    assert payload["items"][0]["quantity"] == 1
    assert payload["billing_data"]["email"] == "test@example.com"
    assert payload["special_reference"].startswith("sukoon-test-")
    target = urlparse(response["Location"])
    assert target.netloc == "accept.paymob.com"
    assert target.path == "/unifiedcheckout/"
    assert parse_qs(target.query)["clientSecret"] == ["sandbox-client-secret"]
    assert "sk_test" not in response["Location"]
    assert response["Cache-Control"] == "no-store"


@pytest.mark.parametrize(
    "key,value",
    [
        ("PAYMOB_TEST_CHECKOUT_ENABLED", False),
        ("PAYMOB_SECRET_KEY", "egy_sk_live_no"),
        ("PAYMOB_PUBLIC_KEY", "egy_pk_live_no"),
        ("PAYMOB_HMAC_SECRET", ""),
        ("PAYMOB_INTEGRATION_ID", ""),
        ("PAYMOB_RETURN_URL", "http://insecure.test/return/"),
    ],
)
def test_disabled_or_live_configuration_cannot_start_checkout(
    client, settings, key, value
):
    setattr(settings, key, value)
    with patch("core_apps.common.paymob_checkout.urlopen") as call:
        assert (
            client.post(reverse("paymob-test-checkout"), details()).status_code == 503
        )
    call.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        {"first_name": ""},
        {"email": "bad"},
        {"phone_number": "01012345678"},
        {"phone_number": "+1234"},
        {"language": "bad"},
    ],
)
def test_invalid_billing_data_does_not_call_provider(client, changes):
    with patch("core_apps.common.paymob_checkout.urlopen") as call:
        assert (
            client.post(reverse("paymob-test-checkout"), details(**changes)).status_code
            == 400
        )
    call.assert_not_called()


@pytest.mark.parametrize(
    "failure",
    [
        URLError("private-provider-details"),
        TimeoutError("private-provider-details"),
        HTTPError(
            "https://accept.paymob.com/v1/intention/",
            401,
            "private-provider-details",
            {},
            None,
        ),
    ],
)
def test_provider_errors_are_safe_and_retryable(client, failure):
    with patch("core_apps.common.paymob_checkout.urlopen", side_effect=failure):
        response = client.post(reverse("paymob-test-checkout"), details(language="ar"))
    assert response.status_code == 502
    assert "private-provider-details" not in response.content.decode()
    assert "تعذّر" in response.content.decode()


def test_missing_provider_client_secret_is_not_redirected(client):
    with patch(
        "core_apps.common.paymob_checkout.urlopen", return_value=io.BytesIO(b"{}")
    ):
        assert (
            client.post(reverse("paymob-test-checkout"), details()).status_code == 502
        )


def test_checkout_rate_limit(client):
    with patch(
        "core_apps.common.paymob_checkout.urlopen", side_effect=URLError("unavailable")
    ) as call:
        for _ in range(5):
            assert (
                client.post(reverse("paymob-test-checkout"), details()).status_code
                == 502
            )
        assert (
            client.post(reverse("paymob-test-checkout"), details()).status_code == 429
        )
    assert call.call_count == 5


def test_checkout_only_accepts_post(client):
    assert client.get(reverse("paymob-test-checkout")).status_code == 405


def test_non_object_json_is_rejected(client):
    assert (
        client.post(
            reverse("paymob-test-checkout"), data="[]", content_type="application/json"
        ).status_code
        == 400
    )
