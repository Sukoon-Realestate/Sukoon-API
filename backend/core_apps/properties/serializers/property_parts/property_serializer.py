"""Property: property serializer."""

import json
from django.utils import timezone
from rest_framework import serializers
from core_apps.profiles.serializers import CloudinarySerializerField
from ...models import City, Governorate, Property, PropertyType
from ..location import PublicUUIDRelatedField
from ...services import PropertyService
from ...rental_inventory import normalize_inventory
from .property_list_serializer import CloudinaryMediaField
from .property_detail_serializer import PropertyDetailSerializer


from .property_serializer_operations.property_validation import PropertyValidationMixin


class PropertySerializer(PropertyValidationMixin, serializers.ModelSerializer):
    """Public service dispatch with domain-specific responsibilities."""

    price = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, default=0
    )
    main_image = CloudinarySerializerField(required=False, allow_null=True)
    main_image_id = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    main_image_name = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    main_image_description = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    video = CloudinaryMediaField(required=False, allow_null=True)
    video_duration = serializers.IntegerField(
        required=False, allow_null=True, min_value=1, max_value=60
    )
    remove_video = serializers.BooleanField(required=False, default=False)
    ownership_proof = CloudinaryMediaField(required=False, allow_null=True)
    remove_ownership_proof = serializers.BooleanField(required=False, default=False)
    amenities = serializers.JSONField(required=False)
    retained_image_ids = serializers.JSONField(required=False)
    images_metadata = serializers.JSONField(required=False)
    building_year = serializers.IntegerField(required=False, allow_null=True)
    deposit = serializers.CharField(required=False, allow_blank=True, default="")
    smoking_allowed = serializers.BooleanField(required=False, allow_null=True)
    floor = serializers.IntegerField(required=False, allow_null=True)
    property_type = serializers.SlugRelatedField(
        slug_field="slug", queryset=PropertyType.objects.all()
    )
    governorate = PublicUUIDRelatedField(queryset=Governorate.objects.all())
    city = PublicUUIDRelatedField(queryset=City.objects.all())
    district = serializers.CharField(required=False, allow_blank=True, default="")
    street = serializers.CharField(required=False, allow_blank=True, default="")
    country = serializers.CharField(required=False, allow_blank=True, default="Egypt")
    rental_inventory = serializers.JSONField(required=False)

    VALID_DEPOSIT_CHOICES = {"none", "half_month", "one_month", "two_months"}

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "description",
            "price",
            "price_period",
            "property_type",
            "is_furnished",
            "bedrooms",
            "bathrooms",
            "area",
            "space",
            "floor",
            "rental_period",
            "suitable_for",
            "smoking_allowed",
            "governorate",
            "city",
            "district",
            "street",
            "country",
            "building_year",
            "deposit",
            "ownership_proof",
            "remove_ownership_proof",
            "latitude",
            "longitude",
            "main_image",
            "main_image_id",
            "main_image_name",
            "main_image_description",
            "video",
            "video_duration",
            "remove_video",
            "amenities",
            "retained_image_ids",
            "images_metadata",
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
            "rental_inventory",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        owner = validated_data.pop("owner", None) or self.context["request"].user
        return PropertyService.create_property(
            owner=owner, validated_data=validated_data
        )

    def update(self, instance, validated_data):
        return PropertyService.update_property(
            property_obj=instance, validated_data=validated_data
        )

    def to_representation(self, instance):
        return PropertyDetailSerializer(instance, context=self.context).data
