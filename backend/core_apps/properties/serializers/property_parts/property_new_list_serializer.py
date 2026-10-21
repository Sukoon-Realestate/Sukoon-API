from core_apps.chat.moderation.property_projection import PropertyPolicyProjection
"""Property: property new list serializer."""

from rest_framework import serializers
from core_apps.profiles.serializers import CloudinarySerializerField
from ...models import Property
from .property_list_serializer import build_rental_summary


class PropertyNewListSerializer(PropertyPolicyProjection, serializers.ModelSerializer):
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
    rental_schema_version = serializers.SerializerMethodField()
    rental_summary = serializers.SerializerMethodField()
    is_sponsored = serializers.BooleanField(read_only=True, default=False)

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
            "rental_schema_version",
            "rental_summary",
            "is_sponsored",
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

        request = self.context.get("request")
        if request:
            accept_lang = request.headers.get("Accept-Language", "").lower()
            lang_param = (request.GET.get("lang") or "").lower()
            if lang_param.startswith("en") or (
                accept_lang.startswith("en") and "ar" not in accept_lang
            ):
                from core_apps.common.translation import translate_tag

                return [translate_tag(t, "en") for t in tags]

        return tags

    def get_rental_schema_version(self, obj: Property):
        return 1 if obj.rental_inventory else None

    def get_rental_summary(self, obj: Property):
        matches = getattr(self.context.get("request"), "student_offer_matches", {})
        return build_rental_summary(obj, matches.get(obj.pk))


class MyPropertyListSerializer(PropertyPolicyProjection, serializers.ModelSerializer):
    """
    Read-only per-property stats for the owner dashboard.
    Requires `views_count` and `visits_count` annotations on the queryset.
    """

    main_image = CloudinarySerializerField(read_only=True)
    views_count = serializers.IntegerField(read_only=True)
    visits_count = serializers.IntegerField(read_only=True)
    rental_scopes = serializers.SerializerMethodField()
    manageable_offer_count = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "main_image",
            "price",
            "price_period",
            "status",
            "is_verified",
            "views_count",
            "visits_count",
            "rental_scopes",
            "manageable_offer_count",
        ]

    def get_rental_scopes(self, obj):
        return [scope for scope in obj.rental_scopes.strip(",").split(",") if scope]

    def get_manageable_offer_count(self, obj):
        return len(
            [
                offer
                for offer in (obj.rental_inventory or {}).get("offers", [])
                if not offer.get("archived")
            ]
        )


class PropertyDetailOwnerSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    name = serializers.CharField(source="get_full_name", read_only=True)
    avatar = CloudinarySerializerField(source="profile.avatar", read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
