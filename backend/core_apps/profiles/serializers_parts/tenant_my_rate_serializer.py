"""Serializers: tenant my rate serializer."""

from typing import Optional
from rest_framework import serializers
from ..models import Contract


class TenantMyRateSerializer(serializers.Serializer):
    """
    Serializer for tenant's submitted review in 'My rates' feed.
    """

    id = serializers.UUIDField(read_only=True)
    property_id = serializers.UUIDField(source="visit.property.id", read_only=True)
    property_title = serializers.CharField(
        source="visit.property.title", read_only=True
    )
    property_image = serializers.SerializerMethodField()
    visit_id = serializers.UUIDField(source="visit.id", read_only=True)
    rating = serializers.IntegerField(source="overall_rating", read_only=True)
    comment = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_property_image(self, obj) -> Optional[str]:
        image = getattr(obj.visit.property, "main_image", None)
        if image and hasattr(image, "url"):
            return image.url
        return str(image) if image else None


class VerificationStatusSerializer(serializers.Serializer):
    """
    Serializer for shared identity verification status.
    Statuses: incomplete, pending, approved, rejected.
    """

    status = serializers.ChoiceField(
        choices=["incomplete", "pending", "approved", "rejected"]
    )
    full_name = serializers.CharField(allow_blank=True)
    submitted_at = serializers.DateTimeField(allow_null=True)
    rejection_reason = serializers.CharField(allow_blank=True, default="")


class TenantContractSerializer(serializers.ModelSerializer):
    """
    Serializer for listing tenant contracts.
    """

    class Meta:
        model = Contract
        fields = [
            "id",
            "property_title",
            "status",
            "start_date",
            "end_date",
            "document_url",
        ]
        read_only_fields = fields
