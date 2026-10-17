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


class PropertyDetailSerializer(PropertyDetailMediaMixin, serializers.ModelSerializer):
    """Public service dispatch with domain-specific responsibilities."""

    images = serializers.SerializerMethodField()
    main_image = CloudinarySerializerField(read_only=True)
    main_image_id = serializers.SerializerMethodField()
    main_image_name = serializers.SerializerMethodField()
    main_image_description = serializers.SerializerMethodField()
    video = CloudinaryMediaField(read_only=True)
    video_duration = serializers.IntegerField(read_only=True)
    property_link = serializers.SerializerMethodField(read_only=True)
    owner = serializers.SerializerMethodField()
    owner_is_verified = serializers.BooleanField(
        source="owner.is_verified", read_only=True
    )
    is_ownership_verified = serializers.BooleanField(read_only=True)
    property_type = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    governorate = GovernorateSerializer(read_only=True)
    city = CitySerializer(read_only=True)
    amenities = serializers.SerializerMethodField()
    is_fav = serializers.BooleanField(read_only=True, default=False)
    is_saved = serializers.BooleanField(read_only=True, default=False)
    rating = serializers.SerializerMethodField()

    def get_rating(self, obj):
        from core_apps.features.services.reputation.visibility import summary
        return summary("property_stay", obj.id)["average"]

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

    class Meta:
        model = Property
        fields = [
            "id",
            "owner",
            "owner_is_verified",
            "is_ownership_verified",
            "main_image",
            "main_image_id",
            "main_image_name",
            "main_image_description",
            "video",
            "video_duration",
            "property_link",
            "title",
            "description",
            "price",
            "price_period",
            "property_type",
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
