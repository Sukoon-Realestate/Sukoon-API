"""Property: property list serializer."""

from typing import Optional
from decimal import Decimal
from rest_framework import serializers
from core_apps.profiles.serializers import CloudinarySerializerField
from ...models import Property, PropertyImage, PropertyType
from .property_collection import PropertyCollectionSerializer, stay_rating


class CloudinaryMediaField(serializers.FileField):
    def to_representation(self, value):
        if not value:
            return None
        if hasattr(value, "url"):
            return value.url
        return str(value)


class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = ["id", "name", "slug", "description"]


class PropertyImageSerializer(serializers.ModelSerializer):
    image = CloudinarySerializerField()
    name = serializers.CharField(required=False, allow_blank=True, default="")
    description = serializers.CharField(required=False, allow_blank=True, default="")

    class Meta:
        model = PropertyImage
        fields = ["id", "image", "name", "description", "created_at", "updated_at"]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["name"] = (instance.name or "").strip()
        ret["description"] = (instance.description or "").strip()
        return ret


class PropertyImageUploadSerializer(serializers.ModelSerializer):
    image = CloudinarySerializerField(required=True)
    name = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
    )
    description = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
    )

    class Meta:
        model = PropertyImage
        fields = ["id", "image", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value):
        return (value or "").strip()

    def validate_description(self, value):
        return (value or "").strip()

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["name"] = (instance.name or "").strip()
        ret["description"] = (instance.description or "").strip()
        return ret


class PropertyImageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["name", "description"]


def build_rental_summary(obj: Property, offer_ids=None):
    if not obj.rental_inventory:
        return None
    from core_apps.features.services.rental_lifecycle.habitability import (
        restricted_keys,
        offer_restricted,
    )

    restricted = (
        obj._listing_restricted_keys
        if hasattr(obj, "_listing_restricted_keys")
        else restricted_keys(obj)
    )
    offers = [
        offer
        for offer in obj.rental_inventory.get("offers", [])
        if (offer_ids is None or str(offer.get("id")) in offer_ids)
        and not offer.get("archived")
        and offer.get("availability") == "available"
        and not offer_restricted(obj, offer, restricted)
    ]
    periods = {offer.get("terms", {}).get("price_period") for offer in offers}
    period = (
        next(iter(periods))
        if offer_ids is not None and len(periods) == 1
        else obj.rental_price_period
    )
    minimum = obj.rental_min_price
    if restricted or offer_ids is not None:
        minimum = min(
            (
                Decimal(str(offer["terms"]["price"]))
                for offer in offers
                if offer.get("terms", {}).get("price") is not None
                and offer.get("terms", {}).get("price_period") == period
            ),
            default=None,
        )
    labels = [offer.get("name", "") for offer in offers]
    scopes = sorted(
        {offer.get("rental_scope") for offer in offers if offer.get("rental_scope")}
    )
    cheapest = None
    if minimum is not None:
        cheapest = next(
            (
                offer
                for offer in offers
                if offer.get("terms", {}).get("price") is not None
                and Decimal(str(offer["terms"]["price"])) == minimum
                and offer["terms"].get("price_period") == period
            ),
            None,
        )
    return {
        "eligible_count": len(offers),
        "scopes": scopes,
        "labels": labels,
        "price": (f"{minimum:.2f}" if minimum is not None else None),
        "price_period": period or None,
        "price_scope": cheapest.get("rental_scope") if cheapest else None,
        "starting_from": len(offers) > 1 and minimum is not None,
    }


class PropertyListSerializer(serializers.ModelSerializer):
    main_image = CloudinarySerializerField(read_only=True)
    images_count = serializers.IntegerField(read_only=True)
    rate = serializers.SerializerMethodField()
    property_type = serializers.SlugRelatedField(
        slug_field="slug", queryset=PropertyType.objects.all()
    )
    is_sponsored = serializers.BooleanField(read_only=True, default=False)
    rental_schema_version = serializers.SerializerMethodField()
    rental_summary = serializers.SerializerMethodField()

    class Meta:
        model = Property
        list_serializer_class = PropertyCollectionSerializer
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
            "is_sponsored",
            "rental_schema_version",
            "rental_summary",
        ]

    def get_rate(self, obj: Property) -> Optional[float]:
        return stay_rating(obj)

    def get_rental_schema_version(self, obj: Property):
        return 1 if obj.rental_inventory else None

    def get_rental_summary(self, obj: Property):
        matches = getattr(self.context.get("request"), "student_offer_matches", {})
        return build_rental_summary(obj, matches.get(obj.pk))
