"""Typed private card-expiry command, reusable outside HTTP."""
from rest_framework import serializers
from . import identity_expiry


class ExpiryInput(serializers.Serializer):
    document_version = serializers.CharField(max_length=64)
    expected_revision = serializers.IntegerField(min_value=0)
    expires_on = serializers.DateField(allow_null=True)
    reminder_days = serializers.ListField(
        child=serializers.ChoiceField(choices=identity_expiry.REMINDER_DAYS), max_length=3
    )

    def validate(self, data):
        if len(set(data["reminder_days"])) != len(data["reminder_days"]):
            raise serializers.ValidationError("Choose each reminder once.")
        if data["reminder_days"] and not data["expires_on"]:
            raise serializers.ValidationError("Enter an expiry date before enabling reminders.")
        return data
