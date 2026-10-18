"""Fixed-price, test-only landing checkout; does not grant entitlements."""

import json
import re
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import serializers
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle


class TestCheckoutThrottle(AnonRateThrottle):
    rate = "5/min"


class TestCheckoutInput(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField(max_length=254)
    phone_number = serializers.RegexField(r"^\+?20\d{10}$", max_length=14)
    language = serializers.ChoiceField(choices=["ar", "en"], default="en")


def test_checkout_ready():
    return (
        settings.PAYMOB_TEST_CHECKOUT_ENABLED
        and settings.PAYMOB_SECRET_KEY.startswith(("egy_sk_test_", "sk_test_"))
        and settings.PAYMOB_PUBLIC_KEY.startswith(("egy_pk_test_", "pk_test_"))
        and bool(settings.PAYMOB_HMAC_SECRET)
        and bool(re.fullmatch(r"[0-9]{1,18}", settings.PAYMOB_INTEGRATION_ID))
        and all(
            urlparse(url).scheme == "https" and bool(urlparse(url).netloc)
            for url in (settings.PAYMOB_WEBHOOK_URL, settings.PAYMOB_RETURN_URL)
        )
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([TestCheckoutThrottle])
def test_checkout(request):
    if not hasattr(request.data, "get"):
        return HttpResponse("Invalid checkout details.", status=400)
    language = "ar" if request.data.get("language") == "ar" else "en"

    def error(status, invalid_details=False):
        return render(
            request,
            "payments/paymob_checkout_error.html",
            {
                "arabic": language == "ar",
                "invalid_details": invalid_details,
                "return_url": f"https://sukoon.rent/{language}#test-subscription",
            },
            status=status,
        )

    if not test_checkout_ready():
        return error(503)
    serializer = TestCheckoutInput(data=request.data)
    if not serializer.is_valid():
        return error(400, invalid_details=True)
    billing = serializer.validated_data.copy()
    billing.pop("language", None)
    billing.update(
        {
            "apartment": "NA",
            "floor": "NA",
            "street": "NA",
            "building": "NA",
            "city": "NA",
            "state": "NA",
            "country": "EG",
            "postal_code": "NA",
        }
    )
    # Price, currency, method and callback URLs are entirely server-controlled.
    payload = {
        "amount": 1000,
        "currency": "EGP",
        "payment_methods": [int(settings.PAYMOB_INTEGRATION_ID)],
        "items": [
            {
                "name": "Sukoon test subscription",
                "amount": 1000,
                "quantity": 1,
                "description": "One-time sandbox test; no renewal or account benefits.",
            }
        ],
        "billing_data": billing,
        "special_reference": f"sukoon-test-{uuid.uuid4()}",
        "expiration": 900,
        "notification_url": settings.PAYMOB_WEBHOOK_URL,
        "redirection_url": settings.PAYMOB_RETURN_URL,
    }
    provider_request = Request(
        "https://accept.paymob.com/v1/intention/",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Token {settings.PAYMOB_SECRET_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(provider_request, timeout=15) as result:
            response = json.load(result)
        client_secret = response.get("client_secret")
        if not isinstance(client_secret, str) or not client_secret:
            return error(502)
    except (HTTPError, URLError, TimeoutError, ValueError, AttributeError):
        # Do not expose Paymob's raw response, request headers or billing data.
        return error(502)
    checkout_url = "https://accept.paymob.com/unifiedcheckout/?" + urlencode(
        {
            "publicKey": settings.PAYMOB_PUBLIC_KEY,
            "clientSecret": client_secret,
        }
    )
    response = HttpResponse(status=303)
    response["Location"] = checkout_url
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response
