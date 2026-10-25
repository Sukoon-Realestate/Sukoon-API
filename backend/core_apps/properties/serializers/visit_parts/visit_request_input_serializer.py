"""Visit request inputs; timing is coordinated by the participants in chat."""

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
    note = serializers.CharField(
        required=False, allow_blank=True, max_length=1000, default=""
    )
    renter_workspace = serializers.ChoiceField(
        choices=["individual", "student"], required=False, default="individual"
    )
    stay_preferences = StayPreferencesSerializer(required=False, allow_null=True)
    viewing_context = ViewingContextSerializer(required=False, write_only=True)
    expected_offer_revision = serializers.IntegerField(
        required=False, write_only=True, min_value=1
    )

    class Meta:
        model = PropertyVisit
        fields = [
            "renter_workspace",
            "id",
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
