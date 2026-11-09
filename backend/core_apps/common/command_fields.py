"""Reusable, strict input contracts for write commands (Sprint 02).

Every write family validates its body through serializers built from these
fields before any lock, idempotency receipt, domain write or provider call.

Policy shared by all commands (see ``sprints/UPLOADS.md`` → *Common command schema*):

* Revisions/counts are integers. Booleans, floats, ``null``, containers and
  non-decimal strings are rejected. Canonical decimal strings (``"3"``) remain
  accepted because historical clients sent multipart/form revisions that the
  old ``int(...)`` coercion accepted.
* Text fields are strings only (DRF's ``CharField`` would silently convert
  numbers) and are bounded.
* Free-form JSON values are bounded in depth, member count and encoded size,
  and must not contain non-finite numbers.
* Date-times must carry an explicit timezone offset.
* Unknown body fields are ignored by the command (DRF default) but remain part
  of the stored replay fingerprint, exactly as before.
"""

import json
import math
import re
import uuid
from decimal import Decimal, InvalidOperation

from django.utils.dateparse import parse_datetime
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

MAX_REVISION = 2**31 - 1
_DECIMAL_INTEGER = re.compile(r"^[0-9]{1,10}$")


def strict_int(value, *, field, minimum=0, maximum=MAX_REVISION):
    """Return ``value`` as an int, rejecting bools, floats and junk."""
    if isinstance(value, str) and _DECIMAL_INTEGER.match(value.strip()):
        value = int(value.strip())
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValidationError(
            {field: f"An integer between {minimum} and {maximum} is required."}
        )
    return value


def parse_revision(data, field="expected_revision", *, default=None, minimum=0):
    """Validate a revision taken from a raw request body.

    ``default`` preserves the historical behavior of commands that treated a
    missing revision as ``0`` (a stale command then still conflicts with 409).
    """
    if not isinstance(data, dict) and not hasattr(data, "get"):
        raise ValidationError("Supply a JSON object.")
    if field not in data:
        if default is None:
            raise ValidationError({field: "This field is required."})
        return default
    return strict_int(data.get(field), field=field, minimum=minimum)


class RevisionField(serializers.Field):
    default_error_messages = {"invalid": "An integer revision is required."}

    def __init__(self, *, minimum=0, maximum=MAX_REVISION, **kwargs):
        self.minimum, self.maximum = minimum, maximum
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            return strict_int(
                data, field="value", minimum=self.minimum, maximum=self.maximum
            )
        except ValidationError:
            raise serializers.ValidationError(
                f"An integer between {self.minimum} and {self.maximum} is required."
            )

    def to_representation(self, value):
        return value


class StrictCharField(serializers.CharField):
    """A ``CharField`` that refuses numbers, booleans and containers."""

    default_error_messages = {"invalid": "Supply text."}

    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid")
        if "\x00" in data:
            raise serializers.ValidationError("Text cannot contain NUL characters.")
        return super().to_internal_value(data)


class RequestKeyField(StrictCharField):
    """Client idempotency key: bounded, non-blank text (UUIDs recommended)."""

    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 100)
        kwargs.setdefault("allow_blank", False)
        super().__init__(**kwargs)


class StrictUUIDField(serializers.UUIDField):
    """UUID text only (DRF also accepts integers and 32-hex forms)."""

    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid", value=data)
        return super().to_internal_value(data)


class UUIDListField(serializers.ListField):
    def __init__(self, *, max_length=25, unique=False, **kwargs):
        self.unique = unique
        super().__init__(child=StrictUUIDField(), max_length=max_length, **kwargs)

    def to_internal_value(self, data):
        values = super().to_internal_value(data)
        if self.unique and len(set(values)) != len(values):
            raise serializers.ValidationError("Identifiers must not repeat.")
        return values


class AwareDateTimeField(serializers.Field):
    """ISO-8601 date-time that must include its timezone offset."""

    default_error_messages = {
        "invalid": "Use an ISO-8601 date-time.",
        "naive": "Include the timezone offset in the date-time.",
    }

    def to_internal_value(self, data):
        if not isinstance(data, str) or len(data) > 64:
            self.fail("invalid")
        try:
            value = parse_datetime(data.strip())
        except ValueError:
            value = None
        if value is None:
            self.fail("invalid")
        if value.tzinfo is None or value.utcoffset() is None:
            self.fail("naive")
        return value

    def to_representation(self, value):
        return value.isoformat() if value else None


def check_json_bounds(value, *, max_depth=4, max_bytes=16_384, max_items=200):
    """Reject oversized, deeply nested or non-finite JSON values."""

    def walk(node, depth):
        if depth > max_depth:
            raise ValidationError("The value is nested too deeply.")
        if isinstance(node, float) and not math.isfinite(node):
            raise ValidationError("Numbers must be finite.")
        if isinstance(node, dict):
            if len(node) > max_items:
                raise ValidationError("The value has too many members.")
            for key, item in node.items():
                if not isinstance(key, str):
                    raise ValidationError("Object keys must be text.")
                walk(item, depth + 1)
        elif isinstance(node, list):
            if len(node) > max_items:
                raise ValidationError("The value has too many items.")
            for item in node:
                walk(item, depth + 1)
        elif not (node is None or isinstance(node, (str, bool, int, float))):
            raise ValidationError("Unsupported value type.")

    walk(value, 0)
    try:
        encoded = json.dumps(value, allow_nan=False, ensure_ascii=False)
    except (TypeError, ValueError):
        raise ValidationError("The value is not valid JSON.")
    if len(encoded.encode("utf-8")) > max_bytes:
        raise ValidationError("The value is too large.")
    return value


class BoundedJSONField(serializers.Field):
    """A JSON value of the listed top-level types, bounded for storage."""

    def __init__(
        self, *, types=(dict, list, str), max_depth=4, max_bytes=16_384, **kwargs
    ):
        self.types, self.max_depth, self.max_bytes = types, max_depth, max_bytes
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if isinstance(data, bool) or not isinstance(data, self.types):
            names = ", ".join(
                {dict: "object", list: "array", str: "text"}.get(t, t.__name__)
                for t in self.types
            )
            raise serializers.ValidationError(f"Use one of: {names}.")
        try:
            return check_json_bounds(
                data, max_depth=self.max_depth, max_bytes=self.max_bytes
            )
        except ValidationError as error:
            raise serializers.ValidationError(error.detail)

    def to_representation(self, value):
        return value


def finite_decimal(value, *, field, max_digits=12, decimal_places=2, minimum=0):
    """Validate a money-like decimal given as text or a JSON number.

    Returns the original value unchanged so stored representations (e.g.
    ``"5000.00"``) keep their exact historical form.
    """
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValidationError({field: "A decimal amount is required."})
    if isinstance(value, str) and (not value.strip() or len(value) > 32):
        raise ValidationError({field: "A decimal amount is required."})
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValidationError({field: "A decimal amount is required."})
    if not number.is_finite():
        raise ValidationError({field: "The amount must be finite."})
    if number < minimum:
        raise ValidationError({field: f"The amount must be at least {minimum}."})
    sign, digits, exponent = number.as_tuple()
    places = max(0, -exponent)
    whole = len(digits) - places if exponent < 0 else len(digits) + exponent
    if places > decimal_places or whole > max_digits - decimal_places:
        raise ValidationError(
            {
                field: f"Use at most {max_digits - decimal_places} whole digits and "
                f"{decimal_places} decimal places."
            }
        )
    return value


def is_uuid(value):
    if not isinstance(value, str):
        return False
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


def require_request_key(data, field="request_key"):
    """Bounded, non-blank text key from a raw body (fits the receipt column)."""
    value = data.get(field) if hasattr(data, "get") else None
    if not isinstance(value, str) or not value.strip() or len(value) > 100:
        raise ValidationError({field: "A request key of at most 100 characters is required."})
    return value


def require_object_body(request):
    """Reject JSON bodies that are arrays, strings, numbers or null."""
    data = request.data
    if not (isinstance(data, dict) or hasattr(data, "getlist")):
        raise ValidationError("Supply a JSON object.")
    return data
