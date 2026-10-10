from rest_framework import serializers


class AdvertisementCreateSerializer(serializers.Serializer):
    operation_id = serializers.CharField(max_length=128)
    plan_id = serializers.CharField(max_length=40)
    plan_revision = serializers.CharField(max_length=32)
    title = serializers.CharField(max_length=150, trim_whitespace=True)
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True,
    )
    banner = serializers.FileField()
    property_id = serializers.UUIDField(required=False, allow_null=True)
    offer_id = serializers.CharField(
        max_length=64, required=False, allow_blank=True, default=""
    )

    def validate(self, attrs):
        if attrs.get("offer_id") and not attrs.get("property_id"):
            raise serializers.ValidationError({"offer_id": ["property_required"]})
        return attrs


class MockPaymentSerializer(serializers.Serializer):
    operation_id = serializers.CharField(max_length=160)
    payment_mode = serializers.ChoiceField(choices=["mock"])
