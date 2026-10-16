from rest_framework import serializers
from .company_serializers import CommandBody, StrictBody
from .portfolio_fields import UnitChanges, UnitDefaults


class UnitVersion(StrictBody):
    id = serializers.UUIDField()
    version = serializers.CharField(max_length=50)


class BulkPreviewBody(CommandBody):
    units = UnitVersion(many=True, allow_empty=False)
    changes = UnitChanges(default=dict)
    inherit_fields = serializers.ListField(
        child=serializers.ChoiceField(choices=list(UnitDefaults().fields)), default=list
    )
    reset_overrides = serializers.BooleanField(default=False)
    reason = serializers.CharField(max_length=1000)

    def validate(self, data):
        if len(data["units"]) > 100 or len({u["id"] for u in data["units"]}) != len(
            data["units"]
        ):
            raise serializers.ValidationError("Choose up to 100 distinct units.")
        if not data["changes"] and not data["inherit_fields"]:
            raise serializers.ValidationError("Choose at least one field to change.")
        if set(data["changes"]) & set(data["inherit_fields"]):
            raise serializers.ValidationError(
                "A field cannot be overridden and inherited together."
            )
        return data


class ReplacementUnit(UnitChanges):
    unit_code = serializers.CharField(max_length=40)
    title = serializers.CharField(max_length=255)
    occupancy_capacity = serializers.IntegerField(
        min_value=1, max_value=1000, allow_null=True
    )


class TopologyPreviewBody(CommandBody):
    operation = serializers.ChoiceField(
        choices=["move_units", "move_building", "split_unit", "merge_units"]
    )
    units = UnitVersion(many=True, default=list)
    target_kind = serializers.ChoiceField(
        choices=["building", "complex"], required=False
    )
    target_id = serializers.UUIDField(required=False)
    target_revision = serializers.IntegerField(min_value=1, required=False)
    replacements = ReplacementUnit(many=True, default=list)
    reason = serializers.CharField(max_length=1000)

    def validate(self, data):
        op, units, replacements = data["operation"], data["units"], data["replacements"]
        if len(units) > 100 or len({u["id"] for u in units}) != len(units):
            raise serializers.ValidationError("Choose distinct units.")
        moving = op.startswith("move_")
        target = {"target_kind", "target_id", "target_revision"}
        if moving and not target <= set(data) or not moving and target & set(data):
            raise serializers.ValidationError(
                "A destination is required only for moves."
            )
        if moving and replacements or op == "move_units" and not units:
            raise serializers.ValidationError("Review the units to move.")
        if op == "move_building" and (units or data.get("target_kind") != "complex"):
            raise serializers.ValidationError("Move a complete building to a complex.")
        if op == "split_unit" and (len(units) != 1 or not 2 <= len(replacements) <= 20):
            raise serializers.ValidationError("Split one unit into 2 to 20 new units.")
        if op == "merge_units" and (len(units) < 2 or len(replacements) != 1):
            raise serializers.ValidationError("Merge selected units into one new unit.")
        if len({r["unit_code"] for r in replacements}) != len(replacements):
            raise serializers.ValidationError("Replacement codes must be unique.")
        return data


class MediaIntentBody(CommandBody):
    purpose = serializers.ChoiceField(choices=["photo", "authority"])
    caption = serializers.CharField(max_length=300, allow_blank=True, default="")
    representative = serializers.BooleanField(default=False)
    sha256 = serializers.RegexField(r"^[a-f0-9]{64}$")
    byte_size = serializers.IntegerField(min_value=1, max_value=5 * 1024 * 1024)
    content_type = serializers.ChoiceField(choices=["image/png", "image/jpeg"])

    def validate(self, data):
        if data["purpose"] == "authority" and data["representative"]:
            raise serializers.ValidationError(
                "Authority evidence cannot be representative media."
            )
        return data


class MediaReviewBody(CommandBody):
    status = serializers.ChoiceField(choices=["approved", "rejected"])
    reason = serializers.CharField(max_length=1000)
