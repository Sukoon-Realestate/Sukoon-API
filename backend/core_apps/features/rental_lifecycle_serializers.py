"""Explicit request contracts; unknown fields never become business state."""

from rest_framework import serializers as s
from .rental_serializers_parts.owner_payment_profile_serializer import (
    RentalTermsSerializer,
)


class StrictSerializer(s.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - set(self.fields):
            raise s.ValidationError({"request": "Unsupported request fields."})
        return super().to_internal_value(data)


class CommandBody(StrictSerializer):
    request_key = s.UUIDField()
    expected_revision = s.IntegerField(min_value=0)


class ProfileBody(CommandBody):
    desired_start = s.DateField(required=False, allow_null=True)
    months = s.IntegerField(min_value=1, max_value=36, required=False, allow_null=True)
    occupants = s.IntegerField(
        min_value=1, max_value=20, required=False, allow_null=True
    )
    introduction = s.CharField(max_length=2000, allow_blank=True, required=False)


class ShareReviewBody(StrictSerializer):
    version_id = s.UUIDField()
    property_id = s.UUIDField()
    categories = s.ListField(
        child=s.ChoiceField(choices=["rental_preferences", "introduction"]),
        allow_empty=False,
        max_length=2,
    )
    expires_at = s.DateTimeField()


class ShareBody(ShareReviewBody, CommandBody):
    consent_digest = s.RegexField(r"^[0-9a-f]{64}$")


class SelectionBody(StrictSerializer):
    offer_id = s.CharField(max_length=64)
    offer_revision = s.IntegerField(min_value=1)
    starts_on = s.DateField(required=False)
    ends_on_exclusive = s.DateField(required=False)

    def validate(self, values):
        start, end = values.get("starts_on"), values.get("ends_on_exclusive")
        if bool(start) != bool(end) or (start and end <= start):
            raise s.ValidationError(
                {"ends_on_exclusive": "Supply a nonempty half-open date range."}
            )
        return values


class HoldBody(SelectionBody, CommandBody):
    property_id = s.UUIDField()
    inventory_revision = s.IntegerField(min_value=1)
    starts_on = s.DateField()
    ends_on_exclusive = s.DateField()
    proposal_id = s.UUIDField(required=False)
    proposal_revision = s.IntegerField(min_value=1, required=False)
    terms_digest = s.RegexField(r"^[0-9a-f]{64}$", required=False)
    kind = s.ChoiceField(choices=["external_booking", "operational"], required=False)
    reason = s.CharField(max_length=2000, required=False, allow_blank=True)


class ReasonBody(CommandBody):
    reason = s.CharField(max_length=2000, required=False, allow_blank=True)


class ConfirmationBody(CommandBody):
    inventory_revision = s.IntegerField(min_value=1)


class FactBody(CommandBody):
    offer_id = s.CharField(max_length=64, allow_blank=True)
    code = s.CharField(max_length=60)
    value = s.CharField(max_length=2000, allow_blank=True)
    classification = s.ChoiceField(
        choices=["owner_reported", "verified", "estimated", "unknown"]
    )
    claim_id = s.UUIDField(required=False, allow_null=True)
    expires_at = s.DateTimeField(required=False, allow_null=True)


class CaseBody(CommandBody):
    reported_started_at = s.DateTimeField(required=False)
    physical_keys = s.ListField(
        child=s.CharField(max_length=100), max_length=100, required=False
    )
    reported_severity = s.ChoiceField(
        choices=["unassessed", "minor", "major", "urgent"], default="unassessed"
    )
    lease_id = s.UUIDField()
    kind = s.ChoiceField(
        choices=[
            "habitability",
            "move_in_mismatch",
            "access_failure",
            "owner_cancellation",
            "tenant_no_show",
            "deposit_dispute",
        ]
    )
    reason = s.CharField(max_length=4000)
    evidence_ids = s.ListField(child=s.UUIDField(), max_length=20, default=list)


class CaseActionBody(CommandBody):
    action = s.ChoiceField(
        choices=["reply", "assign", "triage", "resolve", "reopen", "link_remedy"]
    )
    reason = s.CharField(max_length=4000)
    status = s.CharField(max_length=30, required=False)
    assignee_id = s.UUIDField(required=False)
    refund_id = s.UUIDField(required=False)
    payout_id = s.UUIDField(required=False)
    resolution_code = s.CharField(max_length=40, required=False)
    next_action = s.CharField(max_length=500, required=False)


class ClaimBody(CommandBody):
    subject_kind = s.ChoiceField(
        choices=["identity", "property_authority", "property_fact"]
    )
    subject_user_id = s.UUIDField()
    property_id = s.UUIDField(required=False)
    kyc_submission_id = s.UUIDField(required=False)
    claim_code = s.SlugField(max_length=60)
    public_wording = s.CharField(max_length=240)
    evidence_reference = s.CharField(max_length=160)
    expires_at = s.DateTimeField(required=False, allow_null=True)


class BookingParticipantBody(StrictSerializer):
    tenant_id = s.UUIDField()
    offer_id = s.CharField(max_length=64)
    offer_revision = s.IntegerField(min_value=1)
    terms = RentalTermsSerializer()


class BookingBody(CommandBody):
    application_id = s.UUIDField()
    application_revision = s.IntegerField(min_value=1)
    roster_revision = s.IntegerField(min_value=1)
    booking_model = s.ChoiceField(choices=["independent", "conditional_bundle"])
    deadline = s.DateTimeField()
    participants = BookingParticipantBody(many=True, allow_empty=False)


class ConsentBody(CommandBody):
    decision = s.ChoiceField(choices=["accept", "decline"])
    terms_digest = s.RegexField(r"^[0-9a-f]{64}$")


class AnswerBody(CommandBody):
    field = s.ChoiceField(choices=["included_services", "excluded_services"])
    wording = s.CharField(max_length=500)
    source_message_id = s.UUIDField(required=False)
