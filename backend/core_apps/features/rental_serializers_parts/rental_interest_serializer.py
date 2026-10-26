"""Rental serializers: rental interest serializer."""

from rest_framework import serializers
from ..models import RentalInterest, TermsProposal
from .owner_payment_profile_serializer import RentalTermsSerializer


class RentalInterestSerializer(serializers.ModelSerializer):
    academic_context = serializers.JSONField(source="academic_snapshot", read_only=True)
    application_share_id = serializers.UUIDField(
        source="application_grant.id", read_only=True, allow_null=True
    )
    property_id = serializers.UUIDField(source="property.id", read_only=True)
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)
    tenant_name = serializers.CharField(source="tenant.get_full_name", read_only=True)
    proposal_id = serializers.SerializerMethodField()
    invitation_id = serializers.SerializerMethodField()
    source_eligible = serializers.SerializerMethodField()
    allowed_actions = serializers.SerializerMethodField()
    blocking_reasons = serializers.SerializerMethodField()

    class Meta:
        model = RentalInterest
        fields = [
            "academic_context",
            "desired_end",
            "id",
            "property_id",
            "offer_id",
            "revision",
            "tenant_id",
            "tenant_name",
            "desired_start",
            "months",
            "occupants",
            "message",
            "application_share_id",
            "information_requested",
            "applicant_response",
            "waiting_for",
            "response_due_at",
            "first_owner_response_at",
            "status",
            "proposal_id",
            "invitation_id",
            "offer_snapshot",
            "source_eligible",
            "allowed_actions",
            "blocking_reasons",
        ]

    def get_proposal_id(self, obj):
        proposal = obj.terms_proposals.order_by("-created_at").first()
        return str(proposal.id) if proposal else None

    def get_invitation_id(self, obj):
        invitation = obj.invitations.order_by("-created_at").first()
        return str(invitation.id) if invitation else None

    def get_source_eligible(self, obj):
        return obj.status not in {
            RentalInterest.Status.REJECTED,
            RentalInterest.Status.WITHDRAWN,
        }

    def get_allowed_actions(self, obj):
        from ..services.lease_permissions import interest_actions

        request = self.context.get("request")
        return interest_actions(request.user if request else None, obj)

    def get_blocking_reasons(self, obj):
        return [] if self.get_source_eligible(obj) else ["This interest is closed."]


class RentalDecisionSerializer(serializers.Serializer):
    decision = serializers.CharField(max_length=40)
    note = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    expected_revision = serializers.IntegerField(min_value=1)
    request_key = serializers.UUIDField()
    item_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )
    effective_on = serializers.DateField(required=False)
    requested_date = serializers.DateField(required=False)


class TermsProposalBodySerializer(serializers.Serializer):
    interest_id = serializers.UUIDField()
    offer_id = serializers.CharField(max_length=64)
    terms = RentalTermsSerializer()
    interest_revision = serializers.IntegerField(min_value=1)
    offer_revision = serializers.IntegerField(min_value=1)
    request_key = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=0)
    expires_at = serializers.DateTimeField()
    action = serializers.ChoiceField(choices=["edit_terms", "counter_terms"], default="edit_terms")


class TermsProposalSerializer(serializers.ModelSerializer):
    author_id = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()
    history = serializers.SerializerMethodField()
    decisions = serializers.SerializerMethodField()
    terms_digest = serializers.SerializerMethodField()
    interest_id = serializers.UUIDField(source="interest.id", read_only=True)
    invitation_id = serializers.SerializerMethodField()
    allowed_actions = serializers.SerializerMethodField()
    blocking_reasons = serializers.SerializerMethodField()

    class Meta:
        model = TermsProposal
        fields = [
            "id",
            "interest_id",
            "invitation_id",
            "revision",
            "content_revision",
            "author_id",
            "author_name",
            "expires_at",
            "withdrawal_reason",
            "history",
            "decisions",
            "status",
            "terms",
            "terms_digest",
            "previous_terms",
            "offer_snapshot",
            "allowed_actions",
            "blocking_reasons",
        ]

    def get_author_id(self, obj):
        return str((obj.author or obj.owner).id)

    def get_author_name(self, obj):
        return (obj.author or obj.owner).get_full_name

    def get_history(self, obj):
        return [{
            "version": row.version, "author_id": str(row.author.id), "author_name": row.author.get_full_name,
            "terms": row.terms, "offer_snapshot": row.offer_snapshot,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None, "baseline": row.baseline,
            "created_at": row.created_at.isoformat(),
        } for row in obj.versions.select_related("author").order_by("version")]

    def get_decisions(self, obj):
        from ..models import RentalConsentRecord
        return [{"decision": row.decision, "revision": row.subject_revision,
                 "content_version": row.snapshot.get("content_version"),
                 "actor_name": row.actor.get_full_name, "actor_id": str(row.actor.id),
                 "created_at": row.created_at.isoformat(), "note": row.snapshot.get("note", "")}
                for row in RentalConsentRecord.objects.filter(
                    subject_kind="termsproposal", subject_id=obj.id,
                ).select_related("actor").order_by("created_at", "pk")]

    def to_representation(self, obj):
        value = super().to_representation(obj)
        from ..services.negotiation_terms import is_expired, stage_started
        if obj.status in {"proposed", "changes_requested", "accepted"} and is_expired(obj) and not stage_started(obj):
            value["status"] = "expired"
        return value

    def get_invitation_id(self, obj):
        invitation = obj.invitations.order_by("-created_at").first()
        return str(invitation.id) if invitation else None

    def get_terms_digest(self, obj):
        from ..services.rental_phase2 import fingerprint

        return fingerprint(obj.terms)

    def get_allowed_actions(self, obj):
        from ..services.lease_permissions import proposal_actions

        request = self.context.get("request")
        return proposal_actions(request.user if request else None, obj)

    def get_blocking_reasons(self, obj):
        return (
            []
            if self.get_allowed_actions(obj)
            else ["No action is currently available."]
        )


class RentalInvitationBodySerializer(serializers.Serializer):
    interest_id = serializers.UUIDField()
    interest_revision = serializers.IntegerField(min_value=1)
    property_id = serializers.UUIDField()
    offer_id = serializers.CharField(max_length=64)
    offer_revision = serializers.IntegerField(min_value=1)
    tenant_id = serializers.UUIDField()
    terms_proposal_id = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=0, max_value=0)
    request_key = serializers.UUIDField()


class RentalAgreementDraftBodySerializer(serializers.Serializer):
    invitation_id = serializers.UUIDField()
    invitation_revision = serializers.IntegerField(min_value=1)
    property_id = serializers.UUIDField()
    offer_id = serializers.CharField(max_length=64)
    offer_revision = serializers.IntegerField(min_value=1)
    tenant_id = serializers.UUIDField()
    terms = RentalTermsSerializer()
    request_key = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=0)


class RentalSigningBodySerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    document_hash = serializers.RegexField(r"^[0-9a-f]{64}$")
    expected_revision = serializers.IntegerField(min_value=1)
    request_key = serializers.UUIDField()
