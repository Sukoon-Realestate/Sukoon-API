"""Egypt Paymob transport. Credentials/proofs/provider responses never enter logs."""

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler

from django.conf import settings
from rest_framework.exceptions import APIException, ValidationError

HOST = "https://accept.paymob.com"


class PaymobUnavailable(APIException):
    status_code = 503
    default_detail = (
        "Paymob is temporarily unavailable. Reconcile the original payment."
    )
    default_code = "provider_unavailable"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def credentials_ready():
    return bool(
        settings.PAYMOB_SECRET_KEY.startswith(("egy_sk_test_", "sk_test_"))
        and settings.PAYMOB_PUBLIC_KEY.startswith(("egy_pk_test_", "pk_test_"))
        and settings.PAYMOB_API_KEY
        and settings.PAYMOB_HMAC_SECRET
        and re.fullmatch(r"[0-9]{1,18}", settings.PAYMOB_INTEGRATION_ID)
        and all(
            urlparse(url).scheme == "https"
            and urlparse(url).hostname
            and not urlparse(url).username
            and not urlparse(url).query
            and not urlparse(url).fragment
            for url in (settings.PAYMOB_WEBHOOK_URL, settings.PAYMOB_RETURN_URL)
        )
    )


def sandbox_ready():
    return bool(
        getattr(settings, "RENTAL_RUNTIME_ENVIRONMENT", "production")
        in {"development", "test", "staging"}
        and credentials_ready()
    )


def checkout_ready():
    return bool(
        getattr(settings, "PAYMOB_INVOICE_CHECKOUT_ENABLED", False) and sandbox_ready()
    )


def transport(path, payload=None, *, authorization=""):
    if not credentials_ready():
        raise PaymobUnavailable()
    request = Request(
        HOST + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": authorization} if authorization else {}),
        },
    )
    try:
        with build_opener(NoRedirect()).open(request, timeout=15) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError()
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (HTTPError, URLError, TimeoutError, ValueError, OSError):
        raise PaymobUnavailable() from None


def billing_for(user):
    profile = getattr(user, "profile", None)
    phone = str(getattr(profile, "phone_number", ""))
    if not re.fullmatch(r"\+?20\d{10}", phone):
        raise ValidationError(
            {
                "message": "Add your Egyptian contact phone number before checkout.",
                "code": "billing_details_required",
            }
        )
    return {
        "first_name": user.first_name or "NA",
        "last_name": user.last_name or "NA",
        "email": user.email,
        "phone_number": phone,
        "country": "EG",
        **{
            key: "NA"
            for key in (
                "apartment",
                "floor",
                "street",
                "building",
                "city",
                "state",
                "postal_code",
            )
        },
    }


def billing_for_invoice(user, invoice, quote):
    """Contact selection only; checkout authority is checked before this call.

    Only an admitted, persisted subscription sandbox quote uses synthetic
    gateway data. Never modify the account or send its personal contact there.
    """
    route = quote.purchase_route
    if (
        invoice.purpose == "subscription"
        and invoice.payer_id == user.pk
        and not invoice.organization_id
        and quote.invoice_id == invoice.pk
        and route.get("route") == "hosted_checkout"
        and route.get("enabled") is True
        and route.get("sandbox_only") is True
        and route.get("provider_environment") == "sandbox"
        and route.get("external_checkout_allowed") is True
    ):
        return {
            "first_name": "Test",
            "last_name": "Sandbox",
            "email": "sokoun-payment@example.test",
            "phone_number": "+201010101010",
            "country": "EG",
            **{
                key: "NA"
                for key in (
                    "apartment",
                    "floor",
                    "street",
                    "building",
                    "city",
                    "state",
                    "postal_code",
                )
            },
        }
    return billing_for(user)


def create_intention(payment, billing, return_url):
    attempt = payment.attempt
    return transport(
        "/v1/intention/",
        {
            "amount": attempt.amount_minor,
            "currency": attempt.currency,
            "payment_methods": [int(payment.integration_id)],
            "items": [
                {
                    "name": (
                        "Sukoon subscription sandbox payment"
                        if attempt.invoice.purpose == "subscription"
                        else "Sukoon physical service payment"
                    ),
                    "amount": attempt.amount_minor,
                    "quantity": 1,
                }
            ],
            "billing_data": billing,
            "special_reference": payment.reference,
            "expiration": 900,
            "notification_url": settings.PAYMOB_WEBHOOK_URL,
            "redirection_url": return_url,
        },
        authorization="Token " + settings.PAYMOB_SECRET_KEY,
    )


def inquiry(payment, transaction_id=None):
    token = transport("/api/auth/tokens", {"api_key": settings.PAYMOB_API_KEY}).get(
        "token"
    )
    if not isinstance(token, str) or not token:
        raise PaymobUnavailable()
    if transaction_id:
        if not re.fullmatch(r"[0-9]{1,18}", str(transaction_id)):
            raise PaymobUnavailable()
        return transport(
            f"/api/acceptance/transactions/{transaction_id}",
            authorization="Bearer " + token,
        )
    return transport(
        "/api/ecommerce/orders/transaction_inquiry",
        {"auth_token": token, "merchant_order_id": payment.reference},
    )


def checkout_url(secret):
    if not isinstance(secret, str) or not secret or len(secret) > 300:
        raise PaymobUnavailable()
    return (
        HOST
        + "/unifiedcheckout/?"
        + urlencode({"publicKey": settings.PAYMOB_PUBLIC_KEY, "clientSecret": secret})
    )


def refund_ready():
    return bool(
        getattr(settings, "PAYMOB_REFUNDS_ENABLED", False)
        and credentials_ready()
        and getattr(settings, "RENTAL_RUNTIME_ENVIRONMENT", "production")
        in {"development", "test", "staging"}
    )


def submit_refund(payment, amount):
    if not refund_ready():
        raise PaymobUnavailable()
    return transport(
        "/api/acceptance/void_refund/refund",
        {"transaction_id": int(payment.transaction_id), "amount_cents": amount},
        authorization="Token " + settings.PAYMOB_SECRET_KEY,
    )
