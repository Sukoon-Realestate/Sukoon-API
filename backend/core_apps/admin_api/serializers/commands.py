"""Typed administrative command containers, independent of HTTP view modules."""

from rest_framework import serializers


class ContentCommand(serializers.Serializer):
    expected_revision = serializers.JSONField()
    reason = serializers.CharField(max_length=500)
    values = serializers.DictField()

    def validate_expected_revision(self, value):
        if type(value) is int and 0 <= value <= 2147483647:
            return value
        if isinstance(value, str) and 1 <= len(value) <= 32:
            return value
        raise serializers.ValidationError("Supply the reviewed catalog revision.")


class CampaignPreviewCommand(serializers.Serializer):
    title = serializers.CharField(max_length=180)
    body = serializers.CharField(max_length=2000)
    audience = serializers.ChoiceField(
        choices=["all", "tenants", "landlords", "verified", "students", "companies"],
        default="all",
    )
    request_key = serializers.UUIDField()
