from rest_framework import serializers


class StrictBillingSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError(
                {key: "This field is not accepted." for key in sorted(unknown)}
            )
        return super().to_internal_value(data)


class IssueInvoiceSerializer(StrictBillingSerializer):
    organization_id = serializers.UUIDField(required=False)
    purpose = serializers.ChoiceField(choices=["subscription", "advertising"])
    workspace = serializers.ChoiceField(choices=["tenant", "owner"])
    plan_id = serializers.UUIDField(required=False)
    plan_revision = serializers.IntegerField(min_value=1, required=False)
    advertisement_id = serializers.UUIDField(required=False)
    request_key = serializers.UUIDField()

    def validate(self, attrs):
        required = (
            ("plan_id", "plan_revision")
            if attrs["purpose"] == "subscription"
            else ("advertisement_id",)
        )
        missing = [key for key in required if key not in attrs]
        if missing:
            raise serializers.ValidationError(
                {key: "This field is required." for key in missing}
            )
        # A purchase has one source. Do not silently accept an unrelated source
        # identity (or include it in the idempotency fingerprint).
        unrelated = (
            ("advertisement_id",)
            if attrs["purpose"] == "subscription"
            else ("plan_id", "plan_revision")
        )
        unexpected = [key for key in unrelated if key in attrs]
        if unexpected and self.context.get("mobile_contract"):
            raise serializers.ValidationError(
                {
                    key: "This field does not apply to this purchase purpose."
                    for key in unexpected
                }
            )
        return attrs


class InvoiceActionSerializer(StrictBillingSerializer):
    expected_revision = serializers.IntegerField(min_value=1)
    request_key = serializers.UUIDField()


class PurchaseCheckoutSerializer(InvoiceActionSerializer):
    quote_id = serializers.UUIDField()


class StoreVerifySerializer(StrictBillingSerializer):
    contract_version = serializers.ChoiceField(choices=[1])
    platform = serializers.ChoiceField(choices=["ios", "android"])
    product_id = serializers.CharField(max_length=200)
    transaction_id = serializers.CharField(
        max_length=200, required=False, allow_blank=True
    )
    verification_source = serializers.ChoiceField(choices=["app_store", "google_play"])
    verification_data = serializers.CharField(max_length=262144, trim_whitespace=False)
    proof_digest = serializers.RegexField(r"^[a-f0-9]{64}$")

    def validate(self, attrs):
        expected = "app_store" if attrs["platform"] == "ios" else "google_play"
        if attrs["verification_source"] != expected:
            raise serializers.ValidationError(
                {"verification_source": "The source does not match the platform."}
            )
        return attrs
