from typing import Optional

from rest_framework import serializers

from core_apps.profiles.serializers import CloudinarySerializerField

from ..models import City, Governorate, Property, PropertyImage, PropertyType
from .location import CitySerializer, GovernorateSerializer, PublicUUIDRelatedField
from ..services import PropertyService


class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = ["id", "name", "slug", "description"]


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
    rate = serializers.SerializerMethodField()
    property_type = serializers.SlugRelatedField(
        slug_field="slug", queryset=PropertyType.objects.all()
    )

    class Meta:
        model = Property
        fields = [
            "id",
            "main_image",
            "images_count",
            "title",
            "price",
            "price_period",
            "property_type",
            "area",
            "rate",
        ]

    def get_rate(self, obj: Property) -> Optional[float]:
        # ? Price per square meter; None when area is not provided
        if obj.area:
            return round(float(obj.price) / obj.area, 2)
        return None


class PropertyNewListSerializer(serializers.ModelSerializer):
    """
    Card-style serializer for the new properties feed.

    Returns a compact payload matching the property card UI:
    image, verification badge, title, location, bedrooms, bathrooms,
    area and a short list of translated amenity / restriction tags.
    """

    main_image = CloudinarySerializerField(read_only=True)
    images_count = serializers.IntegerField(read_only=True)
    location = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "main_image",
            "images_count",
            "is_verified",
            "title",
            "location",
            "bedrooms",
            "bathrooms",
            "area",
            "tags",
            "price",
            "price_period",
        ]

    def get_location(self, obj: Property) -> str:
        return f"{obj.district}, {obj.city.name}, {obj.governorate.name}"

    def get_tags(self, obj: Property) -> list[str]:
        # ? Map model flags to Arabic UI chip labels shown on the property card.
        suitable_for_labels = {
            Property.SuitableFor.FAMILIES: "عائلات",
            Property.SuitableFor.SINGLES: "أعزاب",
            Property.SuitableFor.STUDENTS: "طلاب",
            Property.SuitableFor.FEMALE_STUDENTS: "طالبات فقط",
        }

        tags = []
        if obj.suitable_for and obj.suitable_for != Property.SuitableFor.ALL:
            tags.append(suitable_for_labels.get(obj.suitable_for, obj.suitable_for))

        tags.append("ممنوع التدخين" if not obj.smoking_allowed else "مسموح بالتدخين")

        amenity_labels = [
            (obj.has_elevator, "أسانسير"),
            (obj.has_wifi, "واي فاي"),
            (obj.has_air_conditioning, "تكييف"),
            (obj.has_security, "أمن"),
            (obj.has_balcony, "بلكونة"),
            (obj.has_garage, "جراج"),
            (obj.near_metro, "قريب من المترو"),
            (obj.has_natural_gas, "غاز طبيعي"),
        ]
        for active, label in amenity_labels:
            if active:
                tags.append(label)

        return tags


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
            "price_period",
            "status",
            "views_count",
            "visits_count",
        ]


class PropertySerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    main_image = CloudinarySerializerField(required=False, allow_null=True)
    owner = serializers.ReadOnlyField(source="owner.get_full_name")
    property_type = serializers.SlugRelatedField(
        slug_field="slug", queryset=PropertyType.objects.all()
    )
    governorate = PublicUUIDRelatedField(queryset=Governorate.objects.all())
    city = PublicUUIDRelatedField(queryset=City.objects.all())

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
            "governorate",
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
        read_only_fields = ["id", "owner", "is_verified", "created_at", "updated_at"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        city = attrs.get("city", getattr(self.instance, "city", None))
        governorate = attrs.get(
            "governorate", getattr(self.instance, "governorate", None)
        )
        if city and governorate and city.governorate_id != governorate.pkid:
            raise serializers.ValidationError(
                {"city": "The selected city does not belong to this governorate."}
            )
        return attrs

    def create(self, validated_data):
        owner = validated_data.pop("owner", None) or self.context["request"].user
        return PropertyService.create_property(
            owner=owner, validated_data=validated_data
        )

    def update(self, instance, validated_data):
        return PropertyService.update_property(
            property_obj=instance, validated_data=validated_data
        )


class PropertyDetailSerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    main_image = CloudinarySerializerField(read_only=True)
    owner = serializers.ReadOnlyField(source="owner.get_full_name")
    property_type = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    governorate = GovernorateSerializer(read_only=True)
    city = CitySerializer(read_only=True)
    amenities = serializers.SerializerMethodField()
    is_fav = serializers.BooleanField(read_only=True)
    is_saved = serializers.BooleanField(read_only=True)
    rating = serializers.FloatField(read_only=True)

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
            "governorate",
            "city",
            "district",
            "latitude",
            "longitude",
            "amenities",
            "is_fav",
            "is_saved",
            "rating",
            "images",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_amenities(self, obj: Property) -> list[str]:
        return [
            amenity
            for model_field, amenity in self.AMENITY_FIELDS
            if getattr(obj, model_field)
        ]


class AvailablePlacesQuerySerializer(serializers.Serializer):
    property_type_id = serializers.SlugRelatedField(
        slug_field="id", queryset=PropertyType.objects.all(), source="property_type"
    )
