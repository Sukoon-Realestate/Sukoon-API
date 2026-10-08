from django.utils import timezone
from rest_framework import serializers

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
    property_id = serializers.UUIDField(source="property.id", read_only=True)
    property_title = serializers.CharField(source="property.title", read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    tenant_name = serializers.CharField(source="tenant.get_full_name", read_only=True)
    rent = serializers.SerializerMethodField()
    can_sign = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Lease
        fields = [
            "id",
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
        ]

    def get_rent(self, obj):
        return {
            "amount_minor": obj.rent_amount_minor,
            "currency": obj.rent_currency,
            "exponent": obj.rent_exponent,
        }

    def get_can_sign(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and request.user in (obj.owner, obj.tenant)
            and obj.status in {Lease.Status.DRAFT, Lease.Status.PENDING}
        )

    def get_can_cancel(self, obj):
        request = self.context.get("request")
        return bool(
            request and request.user == obj.owner and obj.status == Lease.Status.DRAFT
        )


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
        ]

    def get_amount(self, obj):
        return {
            "amount_minor": obj.amount_minor,
            "currency": obj.currency,
            "exponent": obj.exponent,
        }

    def get_can_pay(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and request.user == obj.lease.tenant
            and obj.status in {RentInvoice.Status.DUE, RentInvoice.Status.OVERDUE}
        )


class RevisionRequestSerializer(serializers.Serializer):
    revision = serializers.IntegerField(min_value=1)
    request_key = serializers.CharField(max_length=100)


class TenancyInvitationCreateSerializer(serializers.Serializer):
    property_id = serializers.UUIDField()
    tenant_id = serializers.UUIDField()
    offer_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    expected_offer_revision = serializers.IntegerField(min_value=1, required=False)
    request_key = serializers.CharField(max_length=100)


class TenancyInvitationResponseSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["accepted", "rejected"])
    revision = serializers.IntegerField(min_value=1)
    request_key = serializers.CharField(max_length=100)


class TenancyInvitationSerializer(serializers.ModelSerializer):
    property_id = serializers.UUIDField(source="property.id", read_only=True)
    property_title = serializers.CharField(source="property.title", read_only=True)
    owner_id = serializers.UUIDField(source="owner.id", read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    tenant_id = serializers.UUIDField(source="tenant.id", read_only=True)
    tenant_name = serializers.CharField(source="tenant.get_full_name", read_only=True)
    lease_id = serializers.UUIDField(source="lease.id", read_only=True, allow_null=True)
    eligible_for_lease = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()

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
