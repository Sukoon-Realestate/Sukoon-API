from django.utils import timezone
from rest_framework import serializers

from .services.lease_permissions import (
    can_cancel_draft,
    can_revoke_invitation,
    is_read_only,
)

from .models import (
    BoostCampaign,
    Lease,
    RentInvoice,
    SearchAlert,
    TenancyInvitation,
)


class BoostCampaignSerializer(serializers.ModelSerializer):
    property_id = serializers.UUIDField(source="property.id", read_only=True)
    property_title = serializers.CharField(source="property.title", read_only=True)

    class Meta:
        model = BoostCampaign
        fields = [
            "id",
            "property_id",
            "property_title",
            "status",
            "duration_days",
            "starts_at",
            "ends_at",
            "impressions",
        ]


class SearchAlertSerializer(serializers.ModelSerializer):
    can_manage = serializers.SerializerMethodField()

    class Meta:
        model = SearchAlert
        fields = [
            "id",
            "name",
            "cadence",
            "enabled",
            "can_manage",
            "revision",
            "last_matched_at",
            "filters",
        ]

    def get_can_manage(self, obj):
        request = self.context.get("request")
        return bool(request and request.user == obj.user and obj.deleted_at is None)


class AlertCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    cadence = serializers.ChoiceField(choices=["instant", "daily"])
    filters = serializers.JSONField()
    request_key = serializers.CharField(max_length=100)

    def validate_filters(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Filters must be an object.")
        allowed_scopes = {"", "entire_property", "room", "room_group", "bed"}
        if value.get("rental_scope", "") not in allowed_scopes:
            raise serializers.ValidationError("Unsupported rental_scope.")
        for key in ("price_min", "price_max"):
            raw = value.get(key)
            if raw not in (None, ""):
                try:
                    if float(raw) < 0:
                        raise ValueError
                except (TypeError, ValueError):
                    raise serializers.ValidationError(
                        f"{key} must be a non-negative number."
                    )
        if value.get("price_min") not in (None, "") and value.get("price_max") not in (
            None,
            "",
        ):
            if float(value["price_min"]) > float(value["price_max"]):
                raise serializers.ValidationError("price_min cannot exceed price_max.")
        if (
            value.get("price_min") not in (None, "")
            or value.get("price_max") not in (None, "")
        ) and not value.get("price_period"):
            raise serializers.ValidationError(
                "price_period is required with price filters."
            )
        return value


class LeaseSerializer(serializers.ModelSerializer):
    owner_id = serializers.UUIDField(source="owner.id", read_only=True)
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)
    legacy_read_only = serializers.SerializerMethodField()
    property_id = serializers.UUIDField(source="property.id", read_only=True)
    property_title = serializers.CharField(source="property.title", read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    tenant_name = serializers.CharField(source="tenant.get_full_name", read_only=True)
    rent = serializers.SerializerMethodField()
    can_sign = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    lease_status = serializers.CharField(source="status", read_only=True)
    allowed_actions = serializers.SerializerMethodField()
    blocking_reasons = serializers.SerializerMethodField()
    invitation_id = serializers.SerializerMethodField()

    class Meta:
        model = Lease
        fields = [
            "id",
            "owner_id",
            "tenant_id",
            "property_id",
            "property_title",
            "owner_name",
            "tenant_name",
            "start_date",
            "end_date",
            "rent",
            "status",
            "revision",
            "document_url",
            "can_sign",
            "can_cancel",
            "offer_id",
            "offer_snapshot",
            "tenancy_root_id",
            "lease_status",
            "occupancy_status",
            "financial_closure_status",
            "legacy_read_only",
            "allowed_actions",
            "blocking_reasons",
            "invitation_id",
            "terms",
            "reviewed_by",
            "document_id",
            "document_hash",
            "hold_expires_at",
        ]

    def get_invitation_id(self, obj):
        invitation = getattr(obj, "tenancy_invitation", None)
        return str(invitation.id) if invitation else None

    def get_rent(self, obj):
        return {
            "amount_minor": obj.rent_amount_minor,
            "currency": obj.rent_currency,
            "exponent": obj.rent_exponent,
        }

    def get_can_sign(self, obj):
        from .services.rental_foundation import fake_provider_available

        request = self.context.get("request")
        return bool(
            request
            and request.user.is_active
            and request.user.is_verified
            and request.user in (obj.owner, obj.tenant)
            and not obj.legacy_read_only
            and fake_provider_available()
            and obj.status == Lease.Status.PENDING_SIGNATURES
            and obj.document_id
        )

    def get_legacy_read_only(self, obj):
        return is_read_only(obj)

    def get_can_cancel(self, obj):
        request = self.context.get("request")
        return bool(request and can_cancel_draft(request.user, obj))

    def get_allowed_actions(self, obj):
        from .services.lease_permissions import agreement_actions

        request = self.context.get("request")
        return agreement_actions(request.user if request else None, obj)

    def get_blocking_reasons(self, obj):
        if self.get_legacy_read_only(obj):
            return ["This legacy agreement is not eligible for new rental mutations."]
        return []


class LeaseCreateSerializer(serializers.Serializer):
    property_id = serializers.UUIDField()
    tenant_id = serializers.UUIDField()
    template_id = serializers.CharField(max_length=80)
    template_version = serializers.CharField(max_length=40)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    rent = serializers.DictField()
    request_key = serializers.CharField(max_length=100)
    offer_id = serializers.CharField(max_length=64, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["end_date"] <= attrs["start_date"]:
            raise serializers.ValidationError(
                {"end_date": "End date must be after start date."}
            )
        rent = attrs["rent"]
        if (
            not isinstance(rent, dict)
            or not isinstance(rent.get("amount_minor"), int)
            or rent["amount_minor"] <= 0
        ):
            raise serializers.ValidationError(
                {"rent": "A positive integer amount_minor is required."}
            )
        if rent.get("currency") != "EGP" or rent.get("exponent", 2) != 2:
            raise serializers.ValidationError(
                {"rent": "Only EGP with exponent 2 is supported."}
            )
        return attrs


class RentInvoiceSerializer(serializers.ModelSerializer):
    billing_period_id = serializers.UUIDField(
        source="billing_period.id", read_only=True
    )
    lease_id = serializers.UUIDField(source="lease.id", read_only=True)
    property_title = serializers.CharField(
        source="lease.property.title", read_only=True
    )
    amount = serializers.SerializerMethodField()
    can_pay = serializers.SerializerMethodField()
    offer_id = serializers.CharField(source="lease.offer_id", read_only=True)
    offer_snapshot = serializers.JSONField(
        source="lease.offer_snapshot", read_only=True
    )
    invoice_status = serializers.CharField(source="status", read_only=True)
    balance = serializers.SerializerMethodField()
    allowed_actions = serializers.SerializerMethodField()
    blocking_reasons = serializers.SerializerMethodField()
    lines = serializers.SerializerMethodField()
    payment_attempt_id = serializers.SerializerMethodField()
    charges = serializers.SerializerMethodField()
    credits = serializers.SerializerMethodField()
    applied = serializers.SerializerMethodField()

    class Meta:
        model = RentInvoice
        fields = [
            "id",
            "lease_id",
            "property_title",
            "reference",
            "due_date",
            "amount",
            "status",
            "receipt_url",
            "can_pay",
            "offer_id",
            "offer_snapshot",
            "revision",
            "invoice_status",
            "balance",
            "allowed_actions",
            "blocking_reasons",
            "invoice_type",
            "billing_period_id",
            "charges",
            "credits",
            "applied",
            "period_start",
            "period_end_exclusive",
            "due_at",
            "deferred_until",
            "lines",
            "payment_attempt_id",
            "receipt_id",
        ]

    def get_amount(self, obj):
        return {
            "amount_minor": obj.amount_minor,
            "currency": obj.currency,
            "exponent": obj.exponent,
        }

    def get_can_pay(self, obj):
        from .services.rental_phase3 import invoice_payment_allowed

        request = self.context.get("request")
        return invoice_payment_allowed(request.user if request else None, obj)

    def _money(self, obj, amount):
        return {
            "amount_minor": amount,
            "currency": obj.currency,
            "exponent": obj.exponent,
        }

    def get_charges(self, obj):
        return self._money(obj, obj.charges_minor)

    def get_credits(self, obj):
        return self._money(obj, obj.credits_minor)

    def get_applied(self, obj):
        return self._money(obj, obj.applied_minor)

    def get_balance(self, obj):
        from .services.rental_phase3 import invoice_balance_minor

        amount = invoice_balance_minor(obj)
        return {
            "amount_minor": amount,
            "currency": obj.currency,
            "exponent": obj.exponent,
        }

    def get_allowed_actions(self, obj):
        return ["quote", "checkout"] if self.get_can_pay(obj) else []

    def get_lines(self, obj):
        return [
            {
                "id": str(line.id),
                "type": line.line_type,
                "description": line.description,
                "amount": {
                    "amount_minor": line.amount_minor,
                    "currency": line.currency,
                    "exponent": line.exponent,
                },
            }
            for line in obj.lines.all()
        ]

    def get_payment_attempt_id(self, obj):
        attempt = obj.payment_attempts.filter(
            payment_status__in=["created", "pending", "authorized"]
        ).first()
        return str(attempt.id) if attempt else None

    def get_blocking_reasons(self, obj):
        from .providers import checkout_available

        if self.get_can_pay(obj):
            return []
        if not checkout_available():
            return ["Secure rent checkout is not available yet."]
        return ["This invoice is not currently payable."]


class RevisionRequestSerializer(serializers.Serializer):
    revision = serializers.IntegerField(min_value=1)
    request_key = serializers.CharField(max_length=100)


class TenancyInvitationCreateSerializer(serializers.Serializer):
    property_id = serializers.UUIDField()
    tenant_id = serializers.UUIDField()
    offer_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    expected_offer_revision = serializers.IntegerField(min_value=1, required=False)
    request_key = serializers.CharField(max_length=100)
    source_visit_id = serializers.UUIDField(required=False)
    source_decision_id = serializers.UUIDField(required=False)


class TenancyInvitationResponseSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["accepted", "rejected"])
    revision = serializers.IntegerField(min_value=1)
    request_key = serializers.CharField(max_length=100)


class TenancyInvitationSerializer(serializers.ModelSerializer):
    source_visit_id = serializers.UUIDField(source="source_visit.id", read_only=True, allow_null=True)
    source_decision_id = serializers.UUIDField(source="source_decision.id", read_only=True, allow_null=True)
    property_id = serializers.UUIDField(source="property.id", read_only=True)
    property_title = serializers.CharField(source="property.title", read_only=True)
    owner_id = serializers.UUIDField(source="owner.id", read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)
    tenant_name = serializers.CharField(source="tenant.get_full_name", read_only=True)
    lease_id = serializers.UUIDField(source="lease.id", read_only=True, allow_null=True)
    eligible_for_lease = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()
    interest_id = serializers.UUIDField(
        source="interest.id", read_only=True, allow_null=True
    )
    terms_proposal_id = serializers.UUIDField(
        source="terms_proposal.id", read_only=True, allow_null=True
    )
    allowed_actions = serializers.SerializerMethodField()
    blocking_reasons = serializers.SerializerMethodField()

    class Meta:
        model = TenancyInvitation
        fields = [
            "id",
            "property_id",
            "property_title",
            "owner_id",
            "owner_name",
            "tenant_id",
            "tenant_name",
            "offer_id",
            "offer_snapshot",
            "status",
            "revision",
            "created_at",
            "expires_at",
            "accepted_at",
            "rejected_at",
            "revoked_at",
            "lease_id",
            "eligible_for_lease",
            "actions",
            "interest_id",
            "terms_proposal_id",
            "consumed_at",
            "allowed_actions",
            "blocking_reasons",
            "source_visit_id",
            "source_decision_id",
            "provenance_version",
        ]

    def get_eligible_for_lease(self, obj):
        from .services.tenancy_invitations import invitation_is_eligible

        return invitation_is_eligible(obj)

    def get_actions(self, obj):
        request = self.context.get("request")
        return {
            "can_respond": bool(
                request
                and request.user == obj.tenant
                and obj.status == TenancyInvitation.Status.PENDING
                and obj.expires_at > timezone.now()
                and request.user.is_active
                and request.user.is_verified
            )
        }

    def get_allowed_actions(self, obj):
        request = self.context.get("request")
        actions = []
        if self.get_actions(obj)["can_respond"]:
            actions.append("respond")
        if can_revoke_invitation(request.user if request else None, obj):
            actions.append("revoke_invitation")
        return actions

    def get_blocking_reasons(self, obj):
        if obj.consumed_at or obj.lease_id:
            return ["This invitation has already been consumed."]
        if obj.expires_at <= timezone.now():
            return ["This invitation has expired."]
        return []
