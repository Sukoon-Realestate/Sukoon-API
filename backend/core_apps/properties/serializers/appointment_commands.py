"""Typed appointment command and day-plan schemas."""

from decimal import Decimal

from zoneinfo import ZoneInfo

from django.utils.dateparse import parse_datetime

from django.utils import timezone

from rest_framework import serializers

from rest_framework.exceptions import ValidationError


class ViewingTimeCommand(serializers.Serializer):
    request_key = serializers.UUIDField()
    action = serializers.ChoiceField(
        choices=["propose", "accept", "reject", "withdraw"]
    )
    expected_visit_revision = serializers.IntegerField(min_value=1, required=False)
    availability_revision = serializers.CharField(max_length=64, required=False)
    slot_ids = serializers.ListField(
        child=serializers.UUIDField(), min_length=1, max_length=3, required=False
    )
    proposal_id = serializers.UUIDField(required=False)
    expected_proposal_revision = serializers.IntegerField(min_value=1, required=False)
    slot_id = serializers.UUIDField(required=False)

    def validate(self, data):
        required = (
            ["expected_visit_revision", "availability_revision", "slot_ids"]
            if data["action"] == "propose"
            else ["proposal_id", "expected_proposal_revision"]
        )
        if data["action"] == "accept":
            required.append("slot_id")
        if any((key not in data for key in required)):
            raise ValidationError("Refresh and select the complete proposal details.")
        if "slot_ids" in data and len(set(data["slot_ids"])) != len(data["slot_ids"]):
            raise ValidationError("Choose distinct viewing times.")
        return data


class ArrivalCommand(serializers.Serializer):
    request_key = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=0)
    expected_visit_revision = serializers.IntegerField(min_value=1)
    active = serializers.BooleanField()
    meeting_point = serializers.CharField(max_length=300, allow_blank=True)
    entrance = serializers.CharField(max_length=300, allow_blank=True)
    instructions = serializers.CharField(max_length=2000, allow_blank=True)
    latitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=7,
        min_value=Decimal("-90"),
        max_value=Decimal("90"),
        allow_null=True,
    )
    longitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=7,
        min_value=Decimal("-180"),
        max_value=Decimal("180"),
        allow_null=True,
    )

    def validate(self, data):
        if (data["latitude"] is None) != (data["longitude"] is None):
            raise ValidationError("Supply both map coordinates, or neither.")
        if data["active"] and (
            not any(
                (data[key] for key in ["meeting_point", "entrance", "instructions"])
            )
        ):
            raise ValidationError(
                "Supply text directions so the card remains useful without maps."
            )
        return data


class StartingPoint(serializers.Serializer):
    latitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=7,
        min_value=Decimal("-90"),
        max_value=Decimal("90"),
    )
    longitude = serializers.DecimalField(
        max_digits=10,
        decimal_places=7,
        min_value=Decimal("-180"),
        max_value=Decimal("180"),
    )


class DayPlanQuery(serializers.Serializer):
    day = serializers.DateField()
    workspace = serializers.ChoiceField(choices=["owner", "individual"])
    viewing_minutes = serializers.IntegerField(min_value=5, max_value=180, default=30)
    buffer_minutes = serializers.IntegerField(min_value=0, max_value=120, default=10)
    mode = serializers.ChoiceField(
        choices=["driving", "walking", "cycling", "transit"], default="driving"
    )
    origin = StartingPoint(required=False)
    start_at = serializers.DateTimeField(required=False)

    def validate_start_at(self, value):
        raw = self.initial_data.get("start_at")
        parsed = parse_datetime(raw) if isinstance(raw, str) else None
        if parsed is None or timezone.is_naive(parsed):
            raise ValidationError(
                "Include an explicit UTC offset for the departure time."
            )
        return value

    def validate(self, data):
        if ("origin" in data) != ("start_at" in data):
            raise ValidationError("A starting point needs an explicit departure time.")
        if (
            "start_at" in data
            and data["start_at"].astimezone(ZoneInfo("Africa/Cairo")).date()
            != data["day"]
        ):
            raise ValidationError(
                "The departure time must fall on the chosen Cairo day."
            )
        return data


class HiddenListingCommand(serializers.Serializer):
    property_id = serializers.UUIDField()
    offer_id = serializers.CharField(max_length=64, allow_blank=True, default="")
    action = serializers.ChoiceField(choices=["hide", "restore"])
    persistent = serializers.BooleanField(default=False)
    expected_revision = serializers.IntegerField(min_value=0)
    property_revision = serializers.IntegerField(min_value=1, required=False)
    offer_revision = serializers.IntegerField(min_value=1, required=False)


class ViewingCommandBody(serializers.Serializer):
    request_key = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=1)
    action = serializers.ChoiceField(choices=["reassign", "accept", "reject", "cancel"])
    representative_membership_id = serializers.UUIDField(required=False)
    note = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=100)
    custom_reason = serializers.CharField(
        required=False, allow_blank=True, max_length=1000
    )

    def validate(self, data):
        if data["action"] == "reassign" and (
            not data.get("representative_membership_id")
        ):
            raise ValidationError(
                {
                    "representative_membership_id": "Choose the current company representative."
                }
            )
        if data["action"] != "reassign" and data.get("representative_membership_id"):
            raise ValidationError(
                {
                    "representative_membership_id": "Only reassignment changes the representative."
                }
            )
        return data
