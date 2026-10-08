import json
from typing import Optional

from django.utils import timezone
from rest_framework import serializers

from core_apps.profiles.serializers import CloudinarySerializerField

from ..models import City, Governorate, Property, PropertyImage, PropertyType
from ..phone_disclosure import counterpart_phone_payload
from .location import CitySerializer, GovernorateSerializer, PublicUUIDRelatedField
from ..services import PropertyService
from ..rental_inventory import normalize_inventory


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


def build_rental_summary(obj: Property):
    if not obj.rental_inventory:
        return None
    offers = [
        offer
        for offer in obj.rental_inventory.get("offers", [])
        if not offer.get("archived") and offer.get("availability") == "available"
    ]
    labels = [offer.get("name", "") for offer in offers]
    scopes = sorted(
        {offer.get("rental_scope") for offer in offers if offer.get("rental_scope")}
    )
    cheapest = None
    if obj.rental_min_price is not None:
        cheapest = next(
            (
                offer
                for offer in offers
                if str(offer.get("terms", {}).get("price"))
                == f"{obj.rental_min_price:.2f}"
            ),
            None,
        )
    return {
        "eligible_count": len(offers),
        "scopes": scopes,
        "labels": labels,
        "price": (
            f"{obj.rental_min_price:.2f}" if obj.rental_min_price is not None else None
        ),
        "price_period": obj.rental_price_period or None,
        "price_scope": cheapest.get("rental_scope") if cheapest else None,
        "starting_from": len(offers) > 1 and obj.rental_min_price is not None,
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
        # ? Price per square meter; None when area is not provided
        if obj.area:
            return round(float(obj.price) / obj.area, 2)
        return None

    def get_rental_schema_version(self, obj: Property):
        return 1 if obj.rental_inventory else None

    def get_rental_summary(self, obj: Property):
        return build_rental_summary(obj)


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
        return build_rental_summary(obj)


class MyPropertyListSerializer(serializers.ModelSerializer):
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


class PropertyDetailSerializer(serializers.ModelSerializer):
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
    rating = serializers.FloatField(read_only=True, default=0.0)
    price = serializers.SerializerMethodField()
    ownership_proof = serializers.SerializerMethodField()
    rental_inventory = serializers.SerializerMethodField()

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
        ]
        read_only_fields = fields

    def get_price(self, obj: Property) -> str:
        return f"{obj.price:.2f}"

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

    def get_ownership_proof(self, obj: Property) -> Optional[str]:
        request = self.context.get("request")
        if (
            not request
            or not getattr(request, "user", None)
            or not request.user.is_authenticated
        ):
            return None
        if request.user == obj.owner or getattr(request.user, "is_staff", False):
            if obj.ownership_proof:
                return getattr(obj.ownership_proof, "url", str(obj.ownership_proof))
        return None

    def get_rental_inventory(self, obj: Property) -> dict:
        inventory = json.loads(json.dumps(obj.rental_inventory or {}))
        request = self.context.get("request")
        is_owner = bool(
            request
            and request.user.is_authenticated
            and (request.user == obj.owner or request.user.is_staff)
        )
        offers = []
        for offer in inventory.get("offers", []):
            if not is_owner and (
                offer.get("archived") or offer.get("availability") != "available"
            ):
                continue
            offer["offer_link"] = (
                f"https://sokoun.app/properties/{obj.id}/offers/{offer.get('id')}"
            )
            if not is_owner:
                offer.pop("actions", None)
            offers.append(offer)
        inventory["offers"] = offers
        return inventory

    def _get_cover_and_images(self, obj: Property):
        all_images = list(obj.images.all())
        main_img_url = ""
        if obj.main_image:
            main_img_url = getattr(obj.main_image, "url", str(obj.main_image))

        cover_img = None
        if main_img_url:
            for img in all_images:
                img_url = getattr(img.image, "url", str(img.image))
                if img_url == main_img_url:
                    cover_img = img
                    break

        if not cover_img and all_images:
            cover_img = all_images[0]

        ordered_images = []
        if cover_img:
            ordered_images.append(cover_img)
            for img in all_images:
                if img.pkid != cover_img.pkid:
                    ordered_images.append(img)
        else:
            ordered_images = all_images

        return cover_img, ordered_images

    def get_main_image_id(self, obj: Property) -> Optional[str]:
        cover_img, _ = self._get_cover_and_images(obj)
        return str(cover_img.id) if cover_img else None

    def get_main_image_name(self, obj: Property) -> str:
        cover_img, _ = self._get_cover_and_images(obj)
        return (cover_img.name or "").strip() if cover_img else ""

    def get_main_image_description(self, obj: Property) -> str:
        cover_img, _ = self._get_cover_and_images(obj)
        return (cover_img.description or "").strip() if cover_img else ""

    def get_images(self, obj: Property) -> list[dict]:
        _, ordered_images = self._get_cover_and_images(obj)
        return PropertyImageSerializer(
            ordered_images, many=True, context=self.context
        ).data


class PropertySerializer(serializers.ModelSerializer):
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

    def validate_deposit(self, value):
        if value is None:
            return ""
        val_str = str(value).strip()
        if not val_str:
            return ""
        if val_str.lower() in self.VALID_DEPOSIT_CHOICES:
            return val_str.lower()
        try:
            num = float(val_str)
            if num < 0:
                raise ValueError()
            return val_str
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                "Deposit must be one of: none, half_month, one_month, two_months, or a non-negative amount."
            )

    def validate_building_year(self, value):
        if value is None or value == "":
            return None
        try:
            val = int(value)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Building year must be an integer.")
        current_year = timezone.now().year
        if val < 1800 or val > current_year:
            raise serializers.ValidationError(
                f"Building year must be between 1800 and {current_year}."
            )
        return val

    def validate_amenities(self, value):
        if value is None or value == "":
            return None
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception:
                raise serializers.ValidationError(
                    "amenities must be a valid JSON array."
                )
        if not isinstance(value, list):
            raise serializers.ValidationError("amenities must be a list of strings.")
        for item in value:
            if item not in PropertyService.SUPPORTED_AMENITIES_MAP:
                raise serializers.ValidationError(f"Unsupported amenity value: {item}")
        return value

    def validate_retained_image_ids(self, value):
        if value is None or value == "":
            return None
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception:
                raise serializers.ValidationError(
                    "retained_image_ids must be a valid JSON array."
                )
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "retained_image_ids must be a list of UUIDs."
            )
        return value

    def validate_images_metadata(self, value):
        if value is None or value == "":
            return None
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception:
                raise serializers.ValidationError(
                    "images_metadata must be a valid JSON array."
                )
        if not isinstance(value, list):
            raise serializers.ValidationError("images_metadata must be a list.")
        for item in value:
            if not isinstance(item, dict) or "id" not in item:
                raise serializers.ValidationError(
                    "Each item in images_metadata must be an object with an 'id' field."
                )
        return value

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
        video_duration = attrs.get("video_duration")
        if video_duration is not None and (video_duration < 1 or video_duration > 60):
            raise serializers.ValidationError(
                {"video_duration": "Video duration must be between 1 and 60 seconds."}
            )
        if attrs.get("remove_video") and attrs.get("video"):
            raise serializers.ValidationError(
                {"video": "Cannot upload video and set remove_video simultaneously."}
            )
        if attrs.get("remove_ownership_proof") and attrs.get("ownership_proof"):
            raise serializers.ValidationError(
                {
                    "ownership_proof": "Cannot upload ownership proof and set remove_ownership_proof simultaneously."
                }
            )
        if "rental_inventory" in attrs:
            attrs["rental_inventory"] = normalize_inventory(
                attrs["rental_inventory"],
                existing=getattr(self.instance, "rental_inventory", None),
            )
        elif not self.instance and "price" not in self.initial_data:
            raise serializers.ValidationError(
                {"price": "This field is required for legacy property listings."}
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

    def to_representation(self, instance):
        return PropertyDetailSerializer(instance, context=self.context).data


class AvailablePlacesQuerySerializer(serializers.Serializer):
    property_type_id = serializers.SlugRelatedField(
        slug_field="id", queryset=PropertyType.objects.all(), source="property_type"
    )


class DailyViewSerializer(serializers.Serializer):
    date = serializers.DateField()
    day = serializers.CharField()
    day_name = serializers.CharField()
    count = serializers.IntegerField()


class TopSearchCriterionSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    percentage = serializers.IntegerField()


class PropertyStatisticsSerializer(serializers.Serializer):
    """
    Detailed analytics for an owner's property listing matching the mobile screen:
    - 4 KPI cards: visit_requests_count, views_count, acceptance_rate, saved_count
    - Period selector (e.g. 30 days)
    - Views last 14 days chart (views_last_14_days)
    - Top search criteria breakdown (top_search_criteria)
    """

    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    period = serializers.CharField(read_only=True)
    period_label = serializers.CharField(read_only=True)

    # 4 Main KPI Cards
    visit_requests_count = serializers.IntegerField(read_only=True)
    views_count = serializers.IntegerField(read_only=True)
    acceptance_rate = serializers.IntegerField(read_only=True)
    saved_count = serializers.IntegerField(read_only=True)

    # 14-day views bar chart
    views_last_14_days = DailyViewSerializer(many=True, read_only=True)

    # Top search criteria breakdown
    top_search_criteria = TopSearchCriterionSerializer(many=True, read_only=True)

    # Extended metrics (backward-compatible)
    visits_count = serializers.IntegerField(read_only=True)
    recent_views_count = serializers.IntegerField(read_only=True)
    upcoming_visits_count = serializers.IntegerField(read_only=True)
    favorites_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    ratings_count = serializers.IntegerField(read_only=True)
    visits_summary = serializers.DictField(
        child=serializers.IntegerField(), read_only=True
    )


class PropertyVisibilitySerializer(serializers.Serializer):
    """
    Serializer to toggle or set property visibility (hidden/active).
    """

    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_hidden = serializers.BooleanField(required=False)
    message = serializers.CharField(read_only=True)
