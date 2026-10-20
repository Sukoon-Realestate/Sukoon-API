from rest_framework import serializers
from .company_serializers import CommandBody


class ExecutionAuthorityBody(CommandBody):
    evidence_reference = serializers.CharField(max_length=200)
    verified_until = serializers.DateTimeField()
    reason = serializers.CharField(max_length=2000)


class TenancyCommandBody(CommandBody):
    role = serializers.CharField(max_length=60, required=False)
    digest = serializers.RegexField(r"^[0-9a-f]{64}$", required=False)
    reason = serializers.CharField(max_length=2000, allow_blank=True, default="")
    decision = serializers.ChoiceField(choices=["accept", "decline"], required=False)
    kind = serializers.CharField(max_length=24, required=False)
    change_id = serializers.UUIDField(required=False)
    assignment_id = serializers.UUIDField(required=False)
    confirmation_id = serializers.UUIDField(required=False)
    employee_id = serializers.UUIDField(required=False)
    property_id = serializers.UUIDField(required=False)
    new_owner_id = serializers.UUIDField(required=False)
    financial_reviewer_id = serializers.UUIDField(required=False)
    ends_on_exclusive = serializers.DateField(required=False)
    rent_minor = serializers.IntegerField(min_value=1, max_value=10**12, required=False)
    possession_on = serializers.DateField(required=False)
    effective_on = serializers.DateField(required=False)
    condition = serializers.DictField(required=False)
    keys = serializers.DictField(required=False)
    meters = serializers.DictField(required=False)
    inventory = serializers.ListField(
        child=serializers.DictField(), max_length=500, required=False
    )
    evidence_ids = serializers.ListField(
        child=serializers.UUIDField(), max_length=5, required=False
    )
    lines = serializers.ListField(
        child=serializers.DictField(), max_length=100, required=False
    )
    signer_mandate_id = serializers.UUIDField(required=False)
    payer_mandate_id = serializers.UUIDField(required=False)
    reviewer_membership_id = serializers.UUIDField(required=False)
    coordinator_membership_id = serializers.UUIDField(required=False)
    title = serializers.CharField(max_length=160, required=False)
    description = serializers.CharField(max_length=5000, required=False)
    category = serializers.CharField(max_length=40, required=False)
    priority = serializers.ChoiceField(
        choices=["normal", "urgent", "emergency"], required=False
    )
    maintenance_id = serializers.UUIDField(required=False)
    maintenance_action = serializers.CharField(max_length=40, required=False)
    appointment_at = serializers.DateTimeField(required=False)
    appointment_ends_at = serializers.DateTimeField(required=False)
    cost_minor = serializers.IntegerField(min_value=1, max_value=10**12, required=False)
    cost_payer = serializers.ChoiceField(choices=["owner", "company"], required=False)


REQUIRED_FIELDS = {
    "commercial_change": [
        "kind",
        "effective_on",
        "ends_on_exclusive",
        "rent_minor",
        "reviewer_membership_id",
        "reason",
    ],
    "ownership_change": ["new_owner_id", "reason"],
    "settlement_adjustment": ["lines", "financial_reviewer_id", "reason"],
    "submit_continuation": ["change_id", "digest"],
    "sign_continuation": ["change_id", "digest", "role"],
    "resume_continuation": ["change_id", "digest"],
    "release_continuation": ["change_id", "digest", "reason"],
    "release_agreement": ["digest", "reason"],
    "review": ["role", "digest"],
    "submit_signature": [],
    "sign": ["digest"],
    "cancel": ["reason"],
    "handover": [
        "kind",
        "possession_on",
        "condition",
        "keys",
        "meters",
        "inventory",
        "evidence_ids",
        "reason",
    ],
    "presence": ["assignment_id", "kind", "possession_on"],
    "presence_respond": ["confirmation_id", "role", "decision"],
    "replace_employee": ["assignment_id", "employee_id", "effective_on", "reason"],
    "respond_change": ["change_id", "role", "decision", "digest"],
    "withdraw_change": ["change_id", "reason"],
    "resume_change": ["change_id"],
    "terminate": ["effective_on", "reason"],
    "settlement": ["lines", "reason"],
    "replace_authority": [
        "signer_mandate_id",
        "payer_mandate_id",
        "reviewer_membership_id",
        "coordinator_membership_id",
        "reason",
    ],
    "maintenance": ["property_id", "title", "description", "category", "priority"],
    "maintenance_action": ["maintenance_id", "maintenance_action", "reason"],
    "reconcile": [],
    "open_case": ["reason"],
    "request_service": ["kind", "reason"],
}


def command_body(action, data):
    if action not in REQUIRED_FIELDS:
        raise serializers.ValidationError("Unsupported company tenancy action.")
    serializer = TenancyCommandBody(data=data)
    serializer.is_valid(raise_exception=True)
    body = serializer.validated_data
    missing = [field for field in REQUIRED_FIELDS[action] if field not in body]
    if missing:
        raise serializers.ValidationError({field: "Required." for field in missing})
    if (
        "reason" in REQUIRED_FIELDS[action] or body.get("decision") == "decline"
    ) and not body.get("reason", "").strip():
        raise serializers.ValidationError({"reason": "Explain this decision."})
    return body
