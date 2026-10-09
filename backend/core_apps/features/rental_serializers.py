from rest_framework import serializers

from .models import (
    Lease,
    OwnerPaymentProfile,
    RentalCommercialPolicy,
    RentalInterest,
    TermsProposal,
)


class MoneySerializer(serializers.Serializer):
    amount_minor = serializers.IntegerField(min_value=0)
    currency = serializers.ChoiceField(choices=["EGP"])
    exponent = serializers.IntegerField(min_value=2, max_value=2)


class RentalTermsSerializer(serializers.Serializer):
    starts_on = serializers.DateField()
    ends_on_exclusive = serializers.DateField()
    handover_on = serializers.DateField()
    monthly_rent = MoneySerializer()
    deposit = MoneySerializer()
    deposit_holder = serializers.ChoiceField(choices=["owner", "platform"])
    included_services = serializers.ListField(child=serializers.CharField(), default=list)
    excluded_services = serializers.ListField(child=serializers.CharField(), default=list)
    termination_policy = serializers.JSONField()
    renewal_policy = serializers.JSONField()
    policy_version = serializers.CharField(max_length=40)
    template_id = serializers.CharField(max_length=80)
    template_version = serializers.CharField(max_length=40)
    timezone = serializers.ChoiceField(choices=["Africa/Cairo"])
    occupants = serializers.IntegerField(min_value=1)
    billing_anchor_day = serializers.IntegerField(min_value=1, max_value=31)
    commission_rate_bps = serializers.IntegerField(min_value=0)
    commission_payer = serializers.ChoiceField(choices=["owner"])
    commission_basis = serializers.ChoiceField(choices=["first_period_base_rent"])
    processing_fee_payer = serializers.ChoiceField(choices=["platform"])
    renewal_commission_rate_bps = serializers.IntegerField(min_value=0)

    def validate(self, attrs):
        if attrs["ends_on_exclusive"] <= attrs["starts_on"]:
            raise serializers.ValidationError(
                {"ends_on_exclusive": "Must be after starts_on."}
            )
        if not attrs["starts_on"] <= attrs["handover_on"] < attrs["ends_on_exclusive"]:
            raise serializers.ValidationError(
                {"handover_on": "Must fall inside the tenancy period."}
            )
        expected = {
            "policy_version": "rental-policy-v1",
            "commission_rate_bps": 1000,
            "renewal_commission_rate_bps": 0,
        }
        for key, value in expected.items():
            if attrs[key] != value:
                raise serializers.ValidationError({key: f"Must be {value}."})
        return attrs


class OwnerPaymentProfileSerializer(serializers.ModelSerializer):
    policy_summary = serializers.SerializerMethodField()
    required_policy_versions = serializers.SerializerMethodField()
    allowed_actions = serializers.SerializerMethodField()
    blocking_reasons = serializers.SerializerMethodField()

    class Meta:
        model = OwnerPaymentProfile
        fields = [
            "id",
            "revision",
            "status",
            "masked_beneficiary",
            "provider",
            "requirements",
            "accepted_policy_versions",
            "policy_summary",
            "required_policy_versions",
            "allowed_actions",
            "blocking_reasons",
        ]

    def get_policy_summary(self, obj):
        policy = RentalCommercialPolicy.objects.filter(
            version="rental-policy-v1", is_active=True
        ).first()
        return policy.summary if policy else {}

    def get_required_policy_versions(self, obj):
        return ["rental-policy-v1"]

    def get_allowed_actions(self, obj):
        return [] if obj.status == OwnerPaymentProfile.Status.READY else ["onboard"]

    def get_blocking_reasons(self, obj):
        reasons = []
        if obj.status != OwnerPaymentProfile.Status.READY:
            reasons.append("Beneficiary onboarding is incomplete.")
        if "rental-policy-v1" not in obj.accepted_policy_versions:
            reasons.append("The required rental policy has not been accepted.")
        return reasons


class OwnerOnboardingBodySerializer(serializers.Serializer):
    expected_revision = serializers.IntegerField(min_value=1)
    request_key = serializers.UUIDField()
    accepted_policy_versions = serializers.ListField(
        child=serializers.CharField(max_length=40), allow_empty=False
    )


class RentalInterestBodySerializer(serializers.Serializer):
    property_id = serializers.UUIDField()
    offer_id = serializers.CharField(max_length=64)
    offer_revision = serializers.IntegerField(min_value=1)
    desired_start = serializers.DateField()
    months = serializers.IntegerField(min_value=1, max_value=60)
    occupants = serializers.IntegerField(min_value=1, max_value=20)
    message = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    request_key = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=0, max_value=0)


class RentalInterestSerializer(serializers.ModelSerializer):
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
        request = self.context.get("request")
        if not request:
            return []
        if request.user == obj.property.owner and self.get_source_eligible(obj):
            return ["create_terms", "reject"]
        if request.user == obj.tenant and obj.status == RentalInterest.Status.SUBMITTED:
            return ["withdraw"]
        return []

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
            "previous_terms",
            "offer_snapshot",
            "allowed_actions",
            "blocking_reasons",
        ]

    def get_invitation_id(self, obj):
        invitation = obj.invitations.order_by("-created_at").first()
        return str(invitation.id) if invitation else None

    def get_allowed_actions(self, obj):
        request = self.context.get("request")
        if not request or request.user not in (obj.owner, obj.interest.tenant):
            return []
        if obj.status in {
            TermsProposal.Status.PROPOSED,
            TermsProposal.Status.CHANGES_REQUESTED,
        }:
            return ["accept", "reject", "request_changes"]
        return []

    def get_blocking_reasons(self, obj):
        return [] if self.get_allowed_actions(obj) else ["No action is currently available."]


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


class LeasePhase2Serializer(serializers.ModelSerializer):
    owner_id = serializers.UUIDField(source="owner.id", read_only=True)
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)
    property_id = serializers.UUIDField(source="property.id", read_only=True)
    property_title = serializers.CharField(source="property.title", read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    tenant_name = serializers.CharField(source="tenant.get_full_name", read_only=True)
    invitation_id = serializers.SerializerMethodField()
    lease_status = serializers.CharField(source="status", read_only=True)
    allowed_actions = serializers.SerializerMethodField()
    blocking_reasons = serializers.SerializerMethodField()

    class Meta:
        model = Lease
        fields = [
            "id",
            "owner_id",
            "tenant_id",
            "invitation_id",
            "property_id",
            "property_title",
            "owner_name",
            "tenant_name",
            "start_date",
            "end_date",
            "status",
            "revision",
            "tenancy_root_id",
            "lease_status",
            "occupancy_status",
            "financial_closure_status",
            "terms",
            "reviewed_by",
            "document_id",
            "document_hash",
            "hold_expires_at",
            "offer_snapshot",
            "legacy_read_only",
            "allowed_actions",
            "blocking_reasons",
        ]

    def get_invitation_id(self, obj):
        invitation = getattr(obj, "tenancy_invitation", None)
        return str(invitation.id) if invitation else None

    def get_allowed_actions(self, obj):
        request = self.context.get("request")
        if not request or request.user not in (obj.owner, obj.tenant):
            return []
        actor_id = str(request.user.id)
        actions = []
        if obj.status == Lease.Status.DRAFT and actor_id not in obj.reviewed_by:
            actions.append("accept_review")
        if (
            request.user == obj.owner
            and obj.status == Lease.Status.DRAFT
            and {str(obj.owner.id), str(obj.tenant.id)}.issubset(set(obj.reviewed_by))
        ):
            actions.append("submit_for_signature")
        if obj.status == Lease.Status.PENDING_SIGNATURES:
            actions.append("sign")
        if request.user == obj.owner and obj.status == Lease.Status.DRAFT:
            actions.append("cancel_draft")
        return actions

    def get_blocking_reasons(self, obj):
        if obj.legacy_read_only:
            return ["This legacy agreement is not eligible for the new workflow."]
        return []
