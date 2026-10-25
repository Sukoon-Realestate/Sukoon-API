"""Validate provider-delivered session keys; never treat them as capture proof."""

import base64
import json
from datetime import datetime, timedelta, timezone as datetime_timezone
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.utils import timezone
from .paymob_client import PaymobUnavailable


def verified_expiry(response, payment, session, redirect, *, allow_expired=False):
    attempt = payment.attempt
    secret = parse_qs(urlparse(session.hosted_url).query).get("clientSecret", [""])[0]
    detail = response.get("intention_detail") or {}
    methods = response.get("payment_methods")
    if (
        response.get("id") != payment.intention_id
        or str(response.get("intention_order_id", response.get("order_id")))
        != payment.order_id
        or response.get("special_reference") != payment.reference
        or response.get("client_secret") != secret
        or detail.get("amount") != attempt.amount_minor
        or detail.get("currency") != attempt.currency
        or response.get("confirmed") is not False
        or response.get("status") != "intended"
        or response.get("paid", False) is not False
        or not isinstance(methods, list)
        or len(methods) != 1
        or str(methods[0].get("integration_id")) != payment.integration_id
        or methods[0].get("live") is not False
        or methods[0].get("currency") != attempt.currency
    ):
        raise PaymobUnavailable()
    if "redirection_url" in response and response["redirection_url"] != redirect:
        raise PaymobUnavailable()
    keys = response.get("payment_keys")
    if isinstance(keys, dict):
        # Retrieve Intention groups keys by method. Its global redirect is the
        # dashboard default; the authenticated card JWT carries the bound URL.
        if keys.get("live") is not False or response.get("redirection_url") != redirect:
            raise PaymobUnavailable()
        keys = [{"key": keys.get("card")}]
    if not isinstance(keys, list) or len(keys) != 1:
        raise PaymobUnavailable()
    expiries = []
    for item in keys:
        raw = item.get("key")
        if not isinstance(raw, str) or len(raw) > 30000:
            raise PaymobUnavailable()
        if raw.count(".") != 2:
            raw = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)).decode()
        encoded = raw.split(".")
        if len(encoded) != 3:
            raise PaymobUnavailable()
        claims = json.loads(
            base64.urlsafe_b64decode(encoded[1] + "=" * (-len(encoded[1]) % 4))
        )
        extra = claims.get("extra") or {}
        bound = claims.get(
            "redirection_url", extra.get("redirection_url", item.get("redirection_url"))
        )
        if (
            bound != redirect
            or str(claims.get("order_id")) != payment.order_id
            or type(claims.get("amount_cents")) is not int
            or claims["amount_cents"] != attempt.amount_minor
            or claims.get("currency") != attempt.currency
            or str(claims.get("integration_id")) != payment.integration_id
            or type(claims.get("exp")) is not int
        ):
            raise PaymobUnavailable()
        for data in (item, claims, extra):
            if "redirection_url" in data and data["redirection_url"] != redirect:
                raise PaymobUnavailable()
            if (
                "notification_url" in data
                and data["notification_url"] != settings.PAYMOB_WEBHOOK_URL
            ):
                raise PaymobUnavailable()
        expiry = datetime.fromtimestamp(claims["exp"], datetime_timezone.utc)
        if expiry > timezone.now() + timedelta(minutes=16) or (
            not allow_expired and expiry <= timezone.now() + timedelta(seconds=15)
        ):
            raise PaymobUnavailable()
        expiries.append(expiry - timedelta(seconds=15))
    return min(expiries)
