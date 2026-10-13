from rest_framework import serializers


class StrictBillingSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: "This field is not accepted." for key in sorted(unknown)})
        return super().to_internal_value(data)


class IssueInvoiceSerializer(StrictBillingSerializer):
    purpose = serializers.ChoiceField(choices=["subscription", "advertising"])
    workspace = serializers.ChoiceField(choices=["tenant", "owner"])
    plan_id = serializers.UUIDField(required=False)
    plan_revision = serializers.IntegerField(min_value=1, required=False)
    advertisement_id = serializers.UUIDField(required=False)
    request_key = serializers.UUIDField()

    def validate(self, attrs):
        required = ("plan_id", "plan_revision") if attrs["purpose"] == "subscription" else ("advertisement_id",)
        missing = [key for key in required if key not in attrs]
        if missing:
            raise serializers.ValidationError({key: "This field is required." for key in missing})
        return attrs


class InvoiceActionSerializer(StrictBillingSerializer):
    expected_revision = serializers.IntegerField(min_value=1)
    request_key = serializers.UUIDField()


class PurchaseCheckoutSerializer(InvoiceActionSerializer):
    quote_id = serializers.UUIDField()
