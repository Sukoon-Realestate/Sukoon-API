from rest_framework import serializers

from core_apps.notifications.models import DeviceToken


class DeviceTokenSerializer(serializers.ModelSerializer):
    """
    Serializer for registering an FCM device token.
    """

    class Meta:
        model = DeviceToken
        fields = ["id", "token", "device_type", "device_name", "is_active", "created_at"]
        read_only_fields = ["id", "is_active", "created_at"]


class DeviceTokenUnregisterSerializer(serializers.Serializer):
    """
    Serializer for unregistering/deactivating an FCM device token.
    """

    token = serializers.CharField(max_length=512, required=True)
