"""Typed rental command bodies (Sprint 02: A3-02, A4-03, A4-04).

Views validate one of these serializers before any lock, receipt or write and
then read only ``validated_data``. The replay fingerprint still uses the raw
request body so receipts stored before this change replay unchanged.

Compatibility notes (recorded in the Sprint 02 results):
* ``expected_revision`` accepts integers and decimal-digit strings; ``true``,
  ``null``, floats, lists and objects now return 400 instead of 500.
* ``request_key`` must be non-blank text of at most 100 characters (the column
  size); maintenance/handover/dispute keys are not forced to be UUIDs because
  the existing contract did not require it.
* Text fields are strings only, bounded by their model columns.
* Unknown fields are ignored, as before.
"""

import re

from rest_framework import serializers

from core_apps.common.command_fields import (
    AwareDateTimeField,
    BoundedJSONField,
    RequestKeyField,
    RevisionField,
    StrictCharField,
    StrictUUIDField,
    UUIDListField,
)

NOTE_MAX = 4000
MAINTENANCE_PRIORITIES = ("low", "normal", "high", "urgent", "emergency")
_SLUG = re.compile(r"^[a-z][a-z0-9_]{0,39}$")


class _RevisionedCommand(serializers.Serializer):
    request_key = RequestKeyField()
    expected_revision = RevisionField()


class MaintenanceCreateCommand(_RevisionedCommand):
    title = StrictCharField(max_length=160, allow_blank=True, trim_whitespace=False)
    description = StrictCharField(
        max_length=NOTE_MAX, allow_blank=True, trim_whitespace=False
    )
    category = StrictCharField(max_length=40)
    priority = serializers.ChoiceField(choices=MAINTENANCE_PRIORITIES)
    # Legacy apps sent one free-text value; current apps send a list of text.
    access_times = serializers.JSONField()
    evidence_ids = UUIDListField(max_length=10)

    def validate_category(self, value):
        if not _SLUG.match(value):
            raise serializers.ValidationError(
                "Use a lowercase category code (letters, digits, underscores)."
            )
        return value

    def validate_access_times(self, value):
        if isinstance(value, str):
            if len(value) > 1000:
                raise serializers.ValidationError("Use at most 1000 characters.")
            return value
        if (
            isinstance(value, list)
            and len(value) <= 10
            and all(isinstance(item, str) and len(item) <= 200 for item in value)
        ):
            return value
        raise serializers.ValidationError(
            "Use an array of at most 10 access-time descriptions (200 characters each)."
        )

    def validate_expected_revision(self, value):
        if value != 0:
            raise serializers.ValidationError("A new request starts at revision 0.")
        return value


class MaintenanceActionCommand(serializers.Serializer):
    request_key = RequestKeyField()
    # Missing revision historically meant 0; a stale command still conflicts.
    expected_revision = RevisionField(required=False, default=0)
    note = StrictCharField(
        max_length=NOTE_MAX, required=False, allow_blank=True, default=""
    )
    appointment_at = AwareDateTimeField(required=False)
    appointment_ends_at = AwareDateTimeField(required=False)
    cost = serializers.DictField(required=False)
    cost_payer = serializers.ChoiceField(choices=("owner", "tenant"), required=False)
    cost_version = RevisionField(minimum=1, required=False)


class HandoverCreateCommand(_RevisionedCommand):
    kind = serializers.ChoiceField(choices=("move_in", "move_out"))
    possession_on = serializers.DateField()
    condition = BoundedJSONField(types=(str, dict))
    keys = BoundedJSONField(types=(str, dict))
    meters = BoundedJSONField(types=(list, dict))
    inventory = BoundedJSONField(types=(list, dict))
    evidence_ids = UUIDListField(max_length=5)

    def validate_expected_revision(self, value):
        if value != 0:
            raise serializers.ValidationError("A new handover starts at revision 0.")
        return value


class HandoverUpdateCommand(serializers.Serializer):
    request_key = RequestKeyField()
    expected_revision = RevisionField(required=False, default=0)
    possession_on = serializers.DateField(required=False)
    condition = BoundedJSONField(types=(str, dict), required=False)
    keys = BoundedJSONField(types=(str, dict), required=False)
    meters = BoundedJSONField(types=(list, dict), required=False)
    inventory = BoundedJSONField(types=(list, dict), required=False)
    evidence_ids = UUIDListField(max_length=5, required=False, default=list)


class HandoverRespondCommand(serializers.Serializer):
    request_key = RequestKeyField()
    expected_revision = RevisionField(required=False, default=0)
    note = StrictCharField(
        max_length=NOTE_MAX, required=False, allow_blank=True, default=""
    )


class DisputeCreateCommand(serializers.Serializer):
    request_key = RequestKeyField()
    expected_revision = RevisionField(required=False)
    lease_id = StrictUUIDField()
    subject_kind = StrictCharField(max_length=40)
    subject_id = StrictUUIDField()
    reason = StrictCharField(
        max_length=NOTE_MAX, required=False, allow_blank=True, default=""
    )
    evidence_ids = UUIDListField(max_length=10, required=False, default=list)


class DisputeRespondCommand(serializers.Serializer):
    request_key = RequestKeyField()
    expected_revision = RevisionField(required=False, default=0)
    note = StrictCharField(
        max_length=NOTE_MAX, required=False, allow_blank=True, default=""
    )


class RentCheckoutCommand(serializers.Serializer):
    invoice_id = StrictUUIDField()
    quote_id = StrictUUIDField()
    request_key = StrictUUIDField()
    expected_revision = RevisionField()


class RefundCreateCommand(serializers.Serializer):
    payment_attempt_id = StrictUUIDField()
    lease_id = StrictUUIDField(required=False, allow_null=True)
    reason = StrictCharField(
        max_length=NOTE_MAX, required=False, allow_blank=True, default=""
    )
    payment_revision = RevisionField(required=False)


class RefundRespondCommand(serializers.Serializer):
    request_key = RequestKeyField()
    expected_revision = RevisionField(required=False, default=0)


def validated(command_class, data):
    """Validate a raw body; non-object bodies get a controlled 400."""
    if not isinstance(data, dict) and not hasattr(data, "getlist"):
        raise serializers.ValidationError("Supply a JSON object.")
    command = command_class(data=data)
    command.is_valid(raise_exception=True)
    return command.validated_data
