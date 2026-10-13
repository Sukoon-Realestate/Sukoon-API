"""Rental serializers: lease phase2 serializer."""

from rest_framework import serializers
from ..models import Lease


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
        from ..services.lease_permissions import agreement_actions

        request = self.context.get("request")
        return agreement_actions(request.user if request else None, obj)

    def get_blocking_reasons(self, obj):
        if obj.legacy_read_only:
            return ["This legacy agreement is not eligible for the new workflow."]
        return []
