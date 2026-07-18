from rest_framework import serializers

from core_apps.profiles.serializers import CloudinarySerializerField

from ..models import Property, PropertyImage
from ..services import PropertyService


class PropertyImageSerializer(serializers.ModelSerializer):
    image = CloudinarySerializerField()

    class Meta:
        model = PropertyImage
        fields = ["id", "image", "name", "description", "created_at", "updated_at"]


class PropertyImageUploadSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)

    class Meta:
        model = PropertyImage
        fields = ["id", "image", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PropertyImageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["name", "description"]


class PropertyListSerializer(serializers.ModelSerializer):
    main_image = CloudinarySerializerField(read_only=True)
    images_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "main_image",
            "images_count",
            "title",
            "description",
            "price",
            "price_period",
            "property_type",
            "is_furnished",
            "is_verified",
            "bedrooms",
            "bathrooms",
            "space",
            "rental_period",
            "suitable_for",
            "smoking_allowed",
            "country",
            "city",
            "district",
            "has_wifi",
            "has_elevator",
            "has_garage",
            "has_security",
            "has_balcony",
            "has_air_conditioning",
            "near_metro",
            "has_natural_gas",
            "has_electricity_meter",
            "has_water_meter",
            "created_at",
            "updated_at",
        ]


class MyPropertyListSerializer(serializers.ModelSerializer):
    """
    Read-only per-property stats for the owner dashboard.
    Requires `views_count` and `visits_count` annotations on the queryset.
    """

    main_image = CloudinarySerializerField(read_only=True)
    views_count = serializers.IntegerField(read_only=True)
    visits_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "main_image",
            "price",
            "status",
            "views_count",
            "visits_count",
        ]


class PropertySerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    main_image = CloudinarySerializerField(required=False, allow_null=True)
    owner = serializers.ReadOnlyField(source="owner.get_full_name")

    class Meta:
        model = Property
        fields = [
            "id",
            "owner",
            "main_image",
            "title",
            "description",
            "price",
            "price_period",
            "property_type",
            "is_furnished",
            "is_verified",
            "bedrooms",
            "bathrooms",
            "area",
            "space",
            "floor",
            "rental_period",
            "suitable_for",
            "smoking_allowed",
            "country",
            "city",
            "district",
            "latitude",
            "longitude",
            "has_wifi",
            "has_elevator",
            "has_garage",
            "has_security",
            "has_balcony",
            "has_air_conditioning",
            "near_metro",
            "has_natural_gas",
            "has_electricity_meter",
            "has_water_meter",
            "images",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        owner = validated_data.pop("owner", None) or self.context["request"].user
        return PropertyService.create_property(
            owner=owner, validated_data=validated_data
        )

    def update(self, instance, validated_data):
        return PropertyService.update_property(
            property_obj=instance, validated_data=validated_data
        )
