from core_apps.chat.moderation.property_projection import PropertyPolicyProjection
"""Property: property detail serializer."""

import json
from typing import Optional
from rest_framework import serializers
from core_apps.profiles.serializers import CloudinarySerializerField
from ...models import Property
from ...phone_disclosure import counterpart_phone_payload
from ..location import CitySerializer, GovernorateSerializer
from .property_list_serializer import CloudinaryMediaField, PropertyImageSerializer
from .property_new_list_serializer import PropertyDetailOwnerSerializer


from .property_detail_serializer_operations.property_detail_media import (
    PropertyDetailMediaMixin,
)


class PropertyDetailSerializer(PropertyPolicyProjection, PropertyDetailMediaMixin, serializers.ModelSerializer):
    """Public service dispatch with domain-specific responsibilities."""

    moderation = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    main_image = CloudinarySerializerField(read_only=True)
    main_image_id = serializers.SerializerMethodField()
    main_image_name = serializers.SerializerMethodField()
    main_image_description = serializers.SerializerMethodField()
    video = CloudinaryMediaField(read_only=True)
    video_duration = serializers.IntegerField(read_only=True)
    video_thumbnail_url = serializers.SerializerMethodField()
    property_link = serializers.SerializerMethodField(read_only=True)
    owner = serializers.SerializerMethodField()
    owner_is_verified = serializers.BooleanField(
        source="owner.is_verified", read_only=True
    )
    is_ownership_verified = serializers.BooleanField(read_only=True)
    property_type = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    property_type_catalog = serializers.SerializerMethodField()
    governorate = GovernorateSerializer(read_only=True)
    city = CitySerializer(read_only=True)
    district_catalog = serializers.UUIDField(
        source="district_catalog.id", read_only=True, allow_null=True
    )
    amenities = serializers.SerializerMethodField()
    is_fav = serializers.BooleanField(read_only=True, default=False)
    is_saved = serializers.BooleanField(read_only=True, default=False)
    rating = serializers.SerializerMethodField()

    def get_rating(self, obj):
        from core_apps.features.services.reputation.visibility import summary

        return summary("property_stay", obj.id)["average"]

    def get_property_type_catalog(self, obj):
        from .property_list_serializer import PropertyTypeSerializer

        return PropertyTypeSerializer(obj.property_type, context=self.context).data

    price = serializers.SerializerMethodField()
    ownership_proof = serializers.SerializerMethodField()
    rental_inventory = serializers.SerializerMethodField()
    virtual_tours = serializers.SerializerMethodField()

    AMENITY_FIELDS = (
        ("has_wifi", "wifi"),
        ("has_elevator", "elevator"),
        ("has_garage", "garage"),
        ("has_security", "security"),
        ("has_balcony", "balcony"),
        ("has_air_conditioning", "air_conditioning"),
        ("near_metro", "near_metro"),
        ("has_natural_gas", "natural_gas"),
        ("has_electricity_meter", "electricity_meter"),
        ("has_water_meter", "water_meter"),
    )

    def get_video_thumbnail_url(self, obj):
        if not obj.video:
            return None
        try:
            return obj.video.build_url(resource_type="video", format="jpg", start_offset="0", secure=True, width=960, crop="limit", quality="auto")
        except (AttributeError, ValueError):
            return None

    class Meta:
        model = Property
        fields = [
            "id",
            "moderation",
            "owner",
            "owner_is_verified",
            "is_ownership_verified",
            "main_image",
            "main_image_id",
            "media_revision",
            "main_image_name",
            "main_image_description",
            "video",
            "video_duration",
            "video_thumbnail_url",
            "property_link",
            "title",
            "description",
            "price",
            "price_period",
            "property_type",
            "property_type_catalog",
            "is_furnished",
            "is_verified",
            "status",
            "bedrooms",
            "bathrooms",
            "area",
            "space",
            "floor",
            "rental_period",
            "suitable_for",
            "smoking_allowed",
            "country",
            "governorate",
            "city",
            "district",
            "district_catalog",
            "street",
            "building_year",
            "deposit",
            "ownership_proof",
            "latitude",
            "longitude",
            "amenities",
            "is_fav",
            "is_saved",
            "rating",
            "images",
            "created_at",
            "updated_at",
            "availability_confirmed_at",
            "rental_inventory",
            "virtual_tours",
        ]
        read_only_fields = fields

    def get_moderation(self, obj):
        request = self.context.get("request")
        if not request or request.user.pk != obj.owner_id:
            return None
        from ...services.moderation import history
        return {"revision": obj.review_revision, "blocked": obj.moderation_blocked,
                "reason": obj.moderation_reason, "history": history(obj)}

    def get_price(self, obj: Property) -> str:
        return f"{obj.price:.2f}"

    def get_virtual_tours(self, obj: Property) -> list:
        from core_apps.virtual_tours.sessions import available

        # General details only contain overview hints. Offer-scoped reads have
        # a separate no-store endpoint and never enter the public listing cache.
        return available(obj)

    def get_owner(self, obj: Property) -> dict:
        owner = PropertyDetailOwnerSerializer(obj.owner).data
        request = self.context.get("request")
        viewer = getattr(request, "user", None)
        owner.update(
            counterpart_phone_payload(
                viewer=viewer,
                counterpart=obj.owner,
                request=request,
                property_obj=obj,
            )
        )
        return owner

    def get_property_link(self, obj: Property) -> str:
        return f"https://sokoun.app/properties/{obj.id}"

    def get_amenities(self, obj: Property) -> list[str]:
        return [
            amenity
            for model_field, amenity in self.AMENITY_FIELDS
            if getattr(obj, model_field, False)
        ]
