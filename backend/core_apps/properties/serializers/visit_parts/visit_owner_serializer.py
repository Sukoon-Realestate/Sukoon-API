"""Visit: visit owner serializer."""

from rest_framework import serializers
from ...phone_disclosure import counterpart_phone_payload
from ...models import Property, PropertyVisitReview
from .property_visit_serializer import User
from .tenant_visit_list_serializer import VisitTenantSerializer


class VisitPropertySummarySerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "location",
            "price",
        ]
        read_only_fields = fields

    def get_location(self, obj):
        return f"{obj.district}, {obj.city.name}"


class VisitOwnerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="get_full_name", read_only=True)
    phone_number = serializers.SerializerMethodField()
    masked_phone_number = serializers.SerializerMethodField()
    is_phone_revealed = serializers.SerializerMethodField()
    phone_notice = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "is_verified",
            "phone_number",
            "masked_phone_number",
            "is_phone_revealed",
            "phone_notice",
        ]
        read_only_fields = fields

    def _contact(self, obj):
        visit = self.context.get("visit")
        viewer = getattr(self.context.get("request"), "user", None)
        if viewer is None and visit is not None:
            viewer = visit.tenant
        return counterpart_phone_payload(
            viewer=viewer,
            counterpart=obj,
            request=self.context.get("request"),
            visit=visit,
        )

    def get_phone_number(self, obj):
        return self._contact(obj)["phone_number"]

    def get_masked_phone_number(self, obj):
        return self._contact(obj)["masked_phone_number"]

    def get_is_phone_revealed(self, obj):
        return self._contact(obj)["is_phone_revealed"]

    def get_phone_notice(self, obj):
        return self._contact(obj)["phone_notice"]


class PropertyVisitReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyVisitReview
        fields = [
            "id",
            "overall_rating",
            "cleanliness_rating",
            "listing_accuracy_rating",
            "owner_interaction_rating",
            "comment",
            "created_at",
        ]
        read_only_fields = ["id", "overall_rating", "created_at"]


class PropertyReviewItemSerializer(serializers.ModelSerializer):
    tenant = VisitTenantSerializer(source="visit.tenant", read_only=True)

    class Meta:
        model = PropertyVisitReview
        fields = [
            "id",
            "tenant",
            "overall_rating",
            "cleanliness_rating",
            "listing_accuracy_rating",
            "owner_interaction_rating",
            "comment",
            "created_at",
        ]
        read_only_fields = fields
