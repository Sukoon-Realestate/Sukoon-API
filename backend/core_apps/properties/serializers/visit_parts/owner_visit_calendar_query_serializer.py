"""Visit: owner visit calendar query serializer."""

from datetime import date, datetime
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from ...models import PropertyVisit
from ...services import PropertyVisitService


class ViewingContextSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(
        choices=["personal", "student", "company"], default="personal"
    )
    company_id = serializers.UUIDField(required=False)
    representative_membership_id = serializers.UUIDField(required=False)
    academic_plan_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if attrs["kind"] == "company" and not all(
            attrs.get(key) for key in ("company_id", "representative_membership_id")
        ):
            raise serializers.ValidationError(
                "Select a company and its current representative."
            )
        return attrs


class StayPreferencesSerializer(serializers.Serializer):
    starts_on = serializers.DateField(required=False)
    ends_on_exclusive = serializers.DateField(required=False)
    occupants = serializers.IntegerField(min_value=1, max_value=20, default=1)

    def to_internal_value(self, data):
        if isinstance(data, dict) and set(data) - {
            "starts_on",
            "ends_on_exclusive",
            "occupants",
        }:
            raise serializers.ValidationError(
                "Only stay dates and occupants may be shared."
            )
        return super().to_internal_value(data)

    def validate(self, attrs):
        start, end = attrs.get("starts_on"), attrs.get("ends_on_exclusive")
        if bool(start) != bool(end) or (start and end <= start):
            raise serializers.ValidationError(
                "Choose both stay dates, with an end after the start."
            )
        if start and start < timezone.localdate():
            raise serializers.ValidationError(
                "The requested stay cannot begin in the past."
            )
        return {
            key: value.isoformat() if isinstance(value, date) else value
            for key, value in attrs.items()
        }


class PropertyVisitCreateSerializer(serializers.ModelSerializer):
    stay_preferences = StayPreferencesSerializer(required=False, allow_null=True)
    viewing_context = ViewingContextSerializer(required=False, write_only=True)
    expected_offer_revision = serializers.IntegerField(
        required=False, write_only=True, min_value=1
    )

    class Meta:
        model = PropertyVisit
        fields = [
            "id",
            "visit_date",
            "visit_time",
            "note",
            "offer_id",
            "expected_offer_revision",
            "viewing_context",
            "stay_preferences",
            "offer_snapshot",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "offer_snapshot", "created_at", "updated_at"]

    def validate_visit_date(self, value):
        from django.utils import timezone

        if value < timezone.localdate():
            raise serializers.ValidationError(_("Visit date cannot be in the past."))
        return value

    def create(self, validated_data):
        tenant = validated_data.pop("tenant")
        property_obj = validated_data.pop("property_obj")
        return PropertyVisitService.create_visit(
            tenant=tenant, property_obj=property_obj, validated_data=validated_data
        )


class PropertyVisitUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyVisit
        fields = ["status"]

    def update(self, instance, validated_data):
        user = self.context["request"].user
        status = validated_data.get("status")
        return PropertyVisitService.update_visit_status(
            user=user, visit_obj=instance, status=status
        )


class AvailableDatesQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=False)


class OwnerAvailabilityWeekQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    week_start = serializers.DateField(required=False)

    def validate(self, attrs):
        if "week_start" in attrs and "start_date" not in attrs:
            attrs["start_date"] = attrs["week_start"]
        return attrs


class OwnerAvailabilitySlotInputSerializer(serializers.Serializer):
    time = serializers.TimeField()
    is_enabled = serializers.BooleanField(default=True)


class OwnerAvailabilityDayUpdateSerializer(serializers.Serializer):
    availability_date = serializers.DateField()
    slots = OwnerAvailabilitySlotInputSerializer(many=True)

    def validate(self, attrs):
        availability_date = attrs["availability_date"]
        now = timezone.localtime()
        slot_times = set()

        for slot in attrs["slots"]:
            slot_time = slot["time"]
            if slot_time in slot_times:
                raise serializers.ValidationError(
                    _("Each time can be submitted only once.")
                )
            if datetime.combine(availability_date, slot_time, now.tzinfo) <= now:
                raise serializers.ValidationError(
                    _("Availability slots must be in the future.")
                )
            slot_times.add(slot_time)
        return attrs


class OwnerVisitCalendarQuerySerializer(serializers.Serializer):
    year = serializers.IntegerField(min_value=2000, max_value=2100)
    month = serializers.IntegerField(min_value=1, max_value=12)
    day = serializers.CharField(required=False, allow_blank=True)
    date = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        year = attrs["year"]
        month = attrs["month"]
        day_raw = attrs.get("day")
        date_raw = attrs.get("date")

        selected_date = None

        # Parse date parameter if provided and not empty
        if date_raw is not None and str(date_raw).strip() != "":
            date_str = str(date_raw).strip()
            if date_str.isdigit():
                day_from_date = int(date_str)
                try:
                    selected_date = date(year, month, day_from_date)
                except ValueError:
                    raise serializers.ValidationError(
                        {"date": _("Invalid day for the specified month and year.")}
                    )
            else:
                try:
                    parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    raise serializers.ValidationError(
                        {
                            "date": _(
                                "Date must be a day number (1-31) or in YYYY-MM-DD format."
                            )
                        }
                    )
                if parsed_date.year != year or parsed_date.month != month:
                    raise serializers.ValidationError(
                        {
                            "date": _(
                                "The selected date must belong to the requested month."
                            )
                        }
                    )
                selected_date = parsed_date

        # Parse day parameter if provided and not empty
        if day_raw is not None and str(day_raw).strip() != "":
            day_str = str(day_raw).strip()
            if not day_str.isdigit():
                raise serializers.ValidationError(
                    {"day": _("Day must be an integer between 1 and 31.")}
                )
            day_num = int(day_str)
            try:
                date_from_day = date(year, month, day_num)
            except ValueError:
                raise serializers.ValidationError(
                    {"day": _("Invalid day for the specified month and year.")}
                )
            if selected_date is not None and selected_date != date_from_day:
                raise serializers.ValidationError(
                    _("Conflicting 'date' and 'day' parameters provided.")
                )
            selected_date = date_from_day

        attrs["date"] = selected_date
        return attrs
