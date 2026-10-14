"""Shared validation for revisioned API commands."""

import uuid

from rest_framework.exceptions import ValidationError


def command_identity(data, *, minimum=0):
    if not isinstance(data, dict):
        raise ValidationError("Supply a JSON object.")
    try:
        request_key = str(uuid.UUID(str(data.get("request_key", ""))))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError({"request_key": "A UUID request key is required."})
    revision = data.get("expected_revision")
    if type(revision) is not int or revision < minimum:
        raise ValidationError(
            {
                "expected_revision": f"An integer revision of at least {minimum} is required."
            }
        )
    return request_key, revision


def money_minor(value, *, allow_negative=False):
    if not isinstance(value, dict):
        raise ValidationError({"amount": "An EGP money object is required."})
    amount = value.get("amount_minor")
    if (
        type(amount) is not int
        or (amount < 0 and not allow_negative)
        or abs(amount) > 10**12
        or value.get("currency", "EGP") != "EGP"
        or value.get("exponent", 2) != 2
    ):
        raise ValidationError(
            {"amount": "Supply integer minor units in EGP with exponent 2."}
        )
    return amount
