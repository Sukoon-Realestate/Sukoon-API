"""Rental serializers: rental interest serializer."""

from rest_framework import serializers
from ..models import RentalInterest, TermsProposal
from .owner_payment_profile_serializer import RentalTermsSerializer


class RentalInterestSerializer(serializers.ModelSerializer):
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


class TermsProposalSerializer(serializers.ModelSerializer):
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
            "status",
            "terms",
            "terms_digest",
            "previous_terms",
            "offer_snapshot",
            "allowed_actions",
            "blocking_reasons",
        ]

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
