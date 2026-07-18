import datetime
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core_apps.properties.serializers.property import PropertyListSerializer
from ..models import PropertyVisit
from ..services import PropertyVisitService


class PropertyVisitSerializer(serializers.ModelSerializer):
    property = PropertyListSerializer(read_only=True)
    tenant_name = serializers.CharField(source="tenant.get_full_name", read_only=True)
    tenant_email = serializers.SerializerMethodField()

    class Meta:
        model = PropertyVisit
        fields = [
            "id",
            "property",
            "tenant_name",
            "tenant_email",
            "visit_date",
            "visit_time",
            "status",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def get_tenant_email(self, obj):
        request = self.context.get("request")
        if request and request.user:
            # Tenant can always see their own email
            if request.user == obj.tenant:
                return obj.tenant.email
            # Owner can only see the tenant's email if the visit is confirmed
            if (
                request.user == obj.property.owner
                and obj.status == PropertyVisit.Status.CONFIRMED
            ):
                return obj.tenant.email
        return ""


class PropertyVisitDetailSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source="tenant.get_full_name", read_only=True)
    tenant_status = serializers.BooleanField(source="tenant.is_verified", read_only=True)

    class Meta:
        model = PropertyVisit
        fields = ["tenant_name", "tenant_status", "visit_date", "status"]
        read_only_fields = fields


class PropertyVisitCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyVisit
        fields = ["id", "visit_date", "visit_time", "note", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_visit_date(self, value):
        if value < datetime.date.today():
            raise serializers.ValidationError(_("Visit date cannot be in the past."))
        return value

    def create(self, validated_data):
        tenant = validated_data.pop("tenant")
        property_obj = validated_data.pop("property_obj")
        return PropertyVisitService.create_visit(
            tenant=tenant, property_obj=property_obj, validated_data=validated_data
        )


class PropertyVisitUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyVisit
        fields = ["status"]

    def update(self, instance, validated_data):
        user = self.context["request"].user
        status = validated_data.get("status")
        return PropertyVisitService.update_visit_status(
            user=user, visit_obj=instance, status=status
        )
