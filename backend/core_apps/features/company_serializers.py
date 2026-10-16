"""Strict discriminated input: hidden fields cannot leak between creation modes."""

from rest_framework import serializers


class StrictBody(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - set(self.fields):
            raise serializers.ValidationError(
                {"non_field_errors": ["The request contains unsupported fields."]}
            )
        return super().to_internal_value(data)


class CommandBody(StrictBody):
    request_key = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=0)


class CompanyBody(CommandBody):
    name = serializers.CharField(max_length=200)
    registration_number = serializers.CharField(max_length=100)
    contact_email = serializers.EmailField()


class ContainerBody(CommandBody):
    kind = serializers.ChoiceField(choices=["building", "complex"])
    name = serializers.CharField(max_length=200)
    code = serializers.CharField(max_length=40)
    address = serializers.CharField(max_length=500)
    description = serializers.CharField(max_length=5000, allow_blank=True, default="")
    facilities = serializers.ListField(
        child=serializers.CharField(max_length=100), max_length=30, default=list
    )
    complex_id = serializers.UUIDField(required=False)
    declared_units = serializers.IntegerField(
        min_value=1, max_value=500, required=False
    )
    floors = serializers.IntegerField(
        min_value=1, max_value=200, required=False, allow_null=True
    )
    declared_buildings = serializers.IntegerField(
        min_value=0, max_value=100, required=False
    )
    declared_standalone_units = serializers.IntegerField(
        min_value=0, max_value=500, required=False
    )

    def validate(self, data):
        if data["kind"] == "building":
            if "declared_units" not in data or set(data) & {
                "declared_buildings",
                "declared_standalone_units",
            }:
                raise serializers.ValidationError(
                    "Building creation requires a declared unit count and building fields only."
                )
        elif (
            set(data) & {"complex_id", "declared_units", "floors"}
            or not {"declared_buildings", "declared_standalone_units"} <= set(data)
            or not (
                data.get("declared_buildings") or data.get("declared_standalone_units")
            )
        ):
            raise serializers.ValidationError(
                "Declare the complex buildings and standalone units, using complex fields only."
            )
        return data


class BatchUnitBody(StrictBody):
    item_key = serializers.UUIDField()
    unit_code = serializers.CharField(max_length=40)
    title = serializers.CharField(max_length=255, required=False)
    bedrooms = serializers.IntegerField(min_value=0, max_value=100, required=False)
    bathrooms = serializers.IntegerField(min_value=1, max_value=100, required=False)
    area = serializers.IntegerField(min_value=1, max_value=100000, required=False)
    floor = serializers.IntegerField(
        min_value=-10, max_value=200, required=False, allow_null=True
    )
    is_furnished = serializers.BooleanField(required=False)
    occupancy_capacity = serializers.IntegerField(
        min_value=1, max_value=1000, allow_null=True
    )


class BatchBody(CommandBody):
    batch_key = serializers.UUIDField()
    template_id = serializers.UUIDField()
    parent_kind = serializers.ChoiceField(
        choices=["building", "complex"], required=False
    )
    parent_id = serializers.UUIDField(required=False)
    units = BatchUnitBody(many=True, allow_empty=False)

    def validate(self, data):
        if ("parent_id" in data) != ("parent_kind" in data):
            raise serializers.ValidationError("Supply both parent kind and identity.")
        if len(data["units"]) > 100 or len(
            {r["item_key"] for r in data["units"]}
        ) != len(data["units"]):
            raise serializers.ValidationError(
                "Submit at most 100 distinctly identified units."
            )
        return data


class InvitationBody(CommandBody):
    email = serializers.EmailField()
    roles = serializers.ListField(
        child=serializers.ChoiceField(
            choices=["admin", "coordinator", "approver", "employee"]
        ),
        allow_empty=False,
        max_length=4,
    )


class AcceptInvitationBody(CommandBody):
    token = serializers.CharField(min_length=32, max_length=200)


class MembershipBody(CommandBody):
    roles = serializers.ListField(
        child=serializers.ChoiceField(
            choices=["admin", "coordinator", "approver", "employee"]
        ),
        max_length=4,
    )
    is_active = serializers.BooleanField()
    can_execute_payments = serializers.BooleanField(required=False)
    reason = serializers.CharField(max_length=1000, allow_blank=True, default="")


class RequestBody(CommandBody):
    title = serializers.CharField(max_length=200)
    purpose = serializers.CharField(max_length=5000)
    cost_center = serializers.CharField(max_length=100, allow_blank=True, default="")
    location = serializers.CharField(max_length=300)
    starts_on = serializers.DateField()
    ends_on_exclusive = serializers.DateField()
    headcount = serializers.IntegerField(min_value=1, max_value=10000)
    commitment_ceiling_minor = serializers.IntegerField(min_value=0, max_value=10**12)
    deposit_limit_minor = serializers.IntegerField(min_value=0, max_value=10**12)

    def validate(self, data):
        if (
            data["ends_on_exclusive"] <= data["starts_on"]
            or (data["ends_on_exclusive"] - data["starts_on"]).days > 3660
        ):
            raise serializers.ValidationError(
                "Select a valid exclusive-end rental interval."
            )
        return data


class OfferBody(CommandBody):
    scope = serializers.ChoiceField(
        choices=[
            "selected_units",
            "entire_building",
            "selected_buildings",
            "entire_complex",
        ]
    )
    building_id = serializers.UUIDField(required=False)
    complex_id = serializers.UUIDField(required=False)
    unit_ids = serializers.ListField(
        child=serializers.UUIDField(), max_length=500, allow_empty=False, required=False
    )
    building_ids = serializers.ListField(
        child=serializers.UUIDField(), max_length=100, allow_empty=False, required=False
    )
    monthly_rent_minor = serializers.IntegerField(min_value=1, max_value=10**12)
    deposit_minor = serializers.IntegerField(min_value=0, max_value=10**12)
    included_services = serializers.ListField(
        child=serializers.CharField(max_length=200), max_length=50, default=list
    )
    excluded_services = serializers.ListField(
        child=serializers.CharField(max_length=200), max_length=50, default=list
    )
    occupancy_policy = serializers.ChoiceField(
        choices=["named_occupants_required", "reserve_capacity_with_notice"],
        default="named_occupants_required",
    )
    publish = serializers.BooleanField(default=False)

    def validate(self, data):
        identity = {
            "selected_units": "unit_ids",
            "entire_building": "building_id",
            "selected_buildings": "building_ids",
            "entire_complex": "complex_id",
        }[data["scope"]]
        if identity not in data or (
            set(data) & {"unit_ids", "building_id", "building_ids", "complex_id"}
        ) != {identity}:
            raise serializers.ValidationError(
                "Supply only the exact identities for the selected scope."
            )
        return data


class SelectionBody(CommandBody):
    offer_id = serializers.UUIDField()
    offer_revision = serializers.IntegerField(min_value=1)
    occupant_ids = serializers.ListField(
        child=serializers.UUIDField(), max_length=1000, default=list
    )
    staff_ids = serializers.ListField(
        child=serializers.UUIDField(), max_length=1000, default=list
    )


class ApprovalBody(CommandBody):
    decision = serializers.ChoiceField(
        choices=["approved", "rejected", "changes_requested"]
    )
    snapshot_digest = serializers.RegexField(r"^[a-f0-9]{64}$")
    reason = serializers.CharField(max_length=1000, allow_blank=True, default="")

    def validate(self, data):
        if data["decision"] != "approved" and not data["reason"].strip():
            raise serializers.ValidationError(
                {"reason": "Explain the rejection or requested changes."}
            )
        return data


class AuthorityReviewBody(CommandBody):
    status = serializers.ChoiceField(choices=["verified", "rejected"])
    evidence_reference = serializers.CharField(max_length=200)
    reason = serializers.CharField(max_length=1000)


class CompanyBudgetBody(CommandBody):
    budget_limit_minor = serializers.IntegerField(
        min_value=0, max_value=10**12, allow_null=True
    )
    deposit_limit_minor = serializers.IntegerField(
        min_value=0, max_value=10**12, allow_null=True
    )
    reason = serializers.CharField(max_length=1000)


class CoordinatorBody(CommandBody):
    coordinator_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=1000)


class AttachUnitBody(CommandBody):
    property_id = serializers.UUIDField()
    inventory_revision = serializers.IntegerField(min_value=0)
    unit_code = serializers.CharField(max_length=40)
    occupancy_capacity = serializers.IntegerField(
        min_value=1, max_value=1000, allow_null=True
    )
