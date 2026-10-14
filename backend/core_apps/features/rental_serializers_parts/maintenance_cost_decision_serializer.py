from rest_framework import serializers


class MaintenanceCostDecisionSerializer(serializers.Serializer):
    """Approval is bound to the proposed cost the responsible payer reviewed."""

    cost_version = serializers.IntegerField(min_value=1)


class MaintenanceAccessTimesSerializer(serializers.Serializer):
    access_times = serializers.JSONField()

    def validate_access_times(self, value):
        # Older apps sent a single free-text value. Keep that variant and its
        # stored replay fingerprint; current mobile sends an array of text.
        if not isinstance(value, str) and not (
            isinstance(value, list) and all(isinstance(item, str) for item in value)
        ):
            raise serializers.ValidationError(
                "Use an array of access-time descriptions."
            )
        return value
