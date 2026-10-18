"""Paymob transaction callback verification; no business fulfilment here."""

import hashlib
import hmac
import re

FIELDS = (
    "amount_cents",
    "created_at",
    "currency",
    "error_occured",
    "has_parent_transaction",
    "id",
    "integration_id",
    "is_3d_secure",
    "is_auth",
    "is_capture",
    "is_refunded",
    "is_standalone_payment",
    "is_voided",
    "order",
    "owner",
    "pending",
    "source_data.pan",
    "source_data.sub_type",
    "source_data.type",
    "success",
)
BOOLEAN_FIELDS = frozenset(
    {
        "error_occured",
        "has_parent_transaction",
        "is_3d_secure",
        "is_auth",
        "is_capture",
        "is_refunded",
        "is_standalone_payment",
        "is_voided",
        "pending",
        "success",
    }
)


def callback_values(data, *, redirect=False):
    """Normalize nested POST and dotted GET fields to Paymob's signing order."""
    if not isinstance(data, dict):
        raise ValueError("Invalid transaction")
    values = {}
    for field in FIELDS:
        if redirect:
            value = data[field]
        elif field == "order":
            value = data["order"]["id"]
        elif field.startswith("source_data."):
            value = data["source_data"][field.split(".")[1]]
        else:
            value = data[field]
        if field in BOOLEAN_FIELDS:
            if redirect:
                if value not in {"true", "false"}:
                    raise ValueError("Invalid boolean")
            elif type(value) is not bool:
                raise ValueError("Invalid boolean")
        elif value is None and field.startswith("source_data."):
            value = ""
        elif type(value) not in (str, int):
            raise ValueError("Invalid callback field")
        values[field] = (
            "true" if value is True else "false" if value is False else str(value)
        )
    for field in ("id", "order", "integration_id", "owner", "amount_cents"):
        if not re.fullmatch(r"[0-9]{1,18}", values[field]):
            raise ValueError("Invalid numeric field")
    return values


def valid_signature(values, signature, secret):
    if not re.fullmatch(r"[0-9a-fA-F]{128}", signature or ""):
        return False
    message = "".join(values[field] for field in FIELDS)
    expected = hmac.new(secret.encode(), message.encode(), hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature.lower())


def reported_status(values):
    if values["is_voided"] == "true":
        return "voided"
    if values["is_refunded"] == "true":
        return "refunded"
    if values["pending"] == "true":
        return "pending"
    if values["success"] != "true" or values["error_occured"] == "true":
        return "failed"
    if values["is_auth"] == "true" and values["is_capture"] != "true":
        return "authorized"
    return "succeeded"
