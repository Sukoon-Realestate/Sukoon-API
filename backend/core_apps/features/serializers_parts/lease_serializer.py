"""Serializers: lease serializer."""

from rest_framework import serializers
from ..services.lease_permissions import can_cancel_draft, is_read_only
from ..models import BoostCampaign, Lease, SearchAlert


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
            "last_checked_at",
            "matching_status",
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
        if "district_ids" in value and not isinstance(value["district_ids"], list):
            raise serializers.ValidationError("district_ids must be a list.")
        if value.get("district_ids"):
            from core_apps.properties.models import City
            from ..services.planning_parts.districts import validate_districts
            from uuid import UUID

            try:
                city = City.objects.get(id=UUID(str(value.get("city", ""))))
            except (ValueError, City.DoesNotExist):
                raise serializers.ValidationError(
                    "Select the catalog city before its districts."
                )
            identities, districts = validate_districts(city, value["district_ids"])
            value = {**value, "district_ids": identities, "districts": districts}
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
        from ..services.rental_foundation import fake_provider_available

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
        from ..services.lease_permissions import agreement_actions

        request = self.context.get("request")
        return agreement_actions(request.user if request else None, obj)

    def get_blocking_reasons(self, obj):
        if self.get_legacy_read_only(obj):
            return ["This legacy agreement is not eligible for new rental mutations."]
        return []
