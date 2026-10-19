from rest_framework import serializers
from .company_serializers import CommandBody, StrictBody


class MandateBody(CommandBody):
    membership_id = serializers.UUIDField()
    kind = serializers.ChoiceField(choices=["sign", "pay"])
    valid_from = serializers.DateTimeField()
    valid_until = serializers.DateTimeField()
    limit_minor = serializers.IntegerField(min_value=1, max_value=10**12)
    evidence_reference = serializers.CharField(max_length=200)
    reason = serializers.CharField(max_length=2000)


class MandateDecisionBody(CommandBody):
    reason = serializers.CharField(max_length=2000)


class PlacementBody(StrictBody):
    employee_id = serializers.UUIDField()
    property_id = serializers.UUIDField()


class PreparationBody(CommandBody):
    signer_mandate_id = serializers.UUIDField()
    payer_mandate_id = serializers.UUIDField()
    placements = PlacementBody(many=True, allow_empty=False)

    def validate_placements(self, value):
        if len(value) > 500 or len({r["employee_id"] for r in value}) != len(value):
            raise serializers.ValidationError(
                "Choose at most 500 distinct named employees."
            )
        return value


class PreparationResponseBody(CommandBody):
    snapshot_digest = serializers.RegexField(r"^[0-9a-f]{64}$")
    role = serializers.ChoiceField(choices=["owner", "signer", "payer", "employee"])
    decision = serializers.ChoiceField(choices=["accepted", "declined", "withdrawn"])
    reason = serializers.CharField(max_length=2000, allow_blank=True, default="")

    def validate(self, value):
        if value["decision"] != "accepted" and not value["reason"].strip():
            raise serializers.ValidationError(
                {"reason": "Explain the declined or withdrawn review."}
            )
        return value
