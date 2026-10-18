from rest_framework import serializers

from core_apps.profiles.serializers import CloudinarySerializerField

from ..models import Property, SavedProperty
from .property_parts.property_collection import (
    PropertyCollectionSerializer,
    stay_rating,
)


class SavedPropertyCardSerializer(serializers.ModelSerializer):
    """Read-only property card used by the tenant's saved screen."""

    main_image = CloudinarySerializerField(read_only=True)
    property_type = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    rating = serializers.SerializerMethodField()

    def get_rating(self, obj):
        return stay_rating(obj)

    saved_at = serializers.DateTimeField(read_only=True)
    is_saved = serializers.SerializerMethodField()
    saved_offers = serializers.SerializerMethodField()

    class Meta:
        model = Property
        list_serializer_class = PropertyCollectionSerializer
        fields = [
            "id",
            "main_image",
            "title",
            "property_type",
            "is_furnished",
            "bedrooms",
            "bathrooms",
            "area",
            "price",
            "price_period",
            "rating",
            "saved_at",
            "is_saved",
            "saved_offers",
        ]
        read_only_fields = fields

    def get_is_saved(self, obj: Property) -> bool:
        return True

    def get_saved_offers(self, obj: Property) -> list[dict]:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return []
        saves = getattr(obj, "current_user_saves", None)
        if saves is None:
            saves = obj.saves.filter(user=request.user)
        return [
            {
                "offer_id": saved.offer_id,
                "offer_snapshot": saved.offer_snapshot,
                "saved_at": saved.created_at.isoformat(),
                "is_saved": True,
            }
            for saved in saves
            if saved.offer_id
        ]


class SavedPropertySerializer(serializers.ModelSerializer):
    """Confirmation payload returned after a property is saved."""

    property_id = serializers.UUIDField(source="property.id", read_only=True)
    saved_at = serializers.DateTimeField(source="created_at", read_only=True)
    is_saved = serializers.SerializerMethodField()
    offer_id = serializers.CharField(read_only=True)

    class Meta:
        model = SavedProperty
        fields = ["id", "property_id", "offer_id", "saved_at", "is_saved"]
        read_only_fields = fields

    def get_is_saved(self, obj: SavedProperty) -> bool:
        return True
