"""Separate Egypt Payouts staging transport. No Accept keys, redirects or Live URL.

Contract references and remaining account validation are documented in
docs/qa/unified-cycles-2026-10-26/PAYOUTS.md in the mobile workspace.
"""

import json
import re
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import Request, build_opener
from urllib.error import HTTPError, URLError

from django.conf import settings
from rest_framework.exceptions import APIException
from .paymob_client import NoRedirect
from .rental_phase2 import fingerprint

HOST = "https://stagingpayouts.paymobsolutions.com"
PROVIDER = "paymob_payouts"
WALLETS = {"vodafone", "etisalat", "orange", "bank_wallet"}
BANKS = {"bank_card"}


class PayoutUnavailable(APIException):
    status_code = 503
    default_detail = (
        "Payout verification is unavailable. Keep the original instruction."
    )
    default_code = "payout_provider_unavailable"


def credentials():
    return {
        field: getattr(settings, "PAYMOB_PAYOUTS_" + field.upper(), "")
        for field in ("client_id", "client_secret", "username", "password")
    }


def account_digest():
    value = credentials()
    return fingerprint(
        {"host": HOST, "client": value["client_id"], "user": value["username"]}
    )


def ready(issuer=None, *, submission=False):
    # Evidence references record account/channel provisioning; flags do not prove
    # a connected transfer. Readiness is deliberately separate from collection.
    return bool(
        getattr(settings, "RENTAL_RUNTIME_ENVIRONMENT", "production")
        in {"development", "test", "staging"}
        and all(credentials().values())
        and getattr(settings, "PAYMOB_PAYOUTS_STAGING_EVIDENCE", "")
        and (
            not submission
            or (
                getattr(settings, "PAYMOB_PAYOUTS_ENABLED", False)
                and issuer in WALLETS | BANKS
                and getattr(settings, "PAYMOB_PAYOUTS_CHANNEL_EVIDENCE", {}).get(issuer)
            )
        )
    )


def transport(path, payload, *, token="", form=False, method="POST"):
    if not ready():
        raise PayoutUnavailable()
    body = urlencode(payload) if form else json.dumps(payload, allow_nan=False)
    request = Request(
        HOST + path,
        data=body.encode(),
        method=method,
        headers={
            "Content-Type": (
                "application/x-www-form-urlencoded" if form else "application/json"
            ),
            **({"Authorization": "Bearer " + token} if token else {}),
        },
    )
    try:
        with build_opener(NoRedirect()).open(request, timeout=15) as response:
            raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError()
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError()
        return data
    except (HTTPError, URLError, TimeoutError, ValueError, OSError):
        # Provider errors may contain credentials and full recipient details.
        raise PayoutUnavailable() from None


def token():
    data = transport(
        "/api/secure/o/token/", {**credentials(), "grant_type": "password"}, form=True
    )
    value = data.get("access_token")
    if (
        data.get("token_type", "").lower() != "bearer"
        or not isinstance(value, str)
        or not re.fullmatch(r"[\x21-\x7e]{1,4096}", value)
    ):
        raise PayoutUnavailable()
    return value


def submit(item, recipient, access_token):
    if not ready(recipient["issuer"], submission=True):
        raise PayoutUnavailable()
    amount = Decimal(item.amount_minor) / 100
    wire_amount = float(amount)
    if Decimal(str(wire_amount)) != amount:
        raise PayoutUnavailable()
    return transport(
        "/api/secure/disburse/",
        {
            **recipient,
            "amount": wire_amount,
            "client_reference_id": str(item.reference),
            "customer_bears_fees": False,
        },
        token=access_token,
    )


def inquire(item, recipient, access_token):
    # Missing references are silently omitted by Paymob: an empty list is NOT
    # evidence that a submission failed or is safe to send again.
    return transport(
        "/api/secure/transaction/inquire/by-reference/",
        {
            "references_list": [str(item.reference)],
            "bank_transactions": recipient["issuer"] in BANKS,
        },
        token=access_token,
        method="GET",
    )
