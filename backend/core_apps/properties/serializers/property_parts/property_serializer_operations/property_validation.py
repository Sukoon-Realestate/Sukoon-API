"""PropertyValidation operations owned by PropertySerializer."""

import json
from django.utils import timezone
from rest_framework import serializers
from core_apps.common.command_fields import finite_decimal, is_uuid
from ....listing_media import LISTING_IMAGE_CAP, measured_seconds
from ....services import PropertyService
from ....rental_inventory import normalize_inventory


class PropertyValidationMixin:
    def validate_deposit(self, value):
        if value is None:
            return ""
        val_str = str(value).strip()
        if not val_str:
            return ""
        if val_str.lower() in self.VALID_DEPOSIT_CHOICES:
            return val_str.lower()
        try:
            # "nan"/"inf" were accepted by float(); amounts must be finite.
            finite_decimal(val_str, field="deposit")
            return val_str
        except (ValueError, TypeError, serializers.ValidationError):
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
        if not isinstance(value, list) or len(value) > 50:
            raise serializers.ValidationError("amenities must be a list of strings.")
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("amenities must be a list of strings.")
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
        if (
            not isinstance(value, list)
            or len(value) > LISTING_IMAGE_CAP
            or not all(is_uuid(item) for item in value)
        ):
            raise serializers.ValidationError(
                "retained_image_ids must be a list of UUIDs."
            )
        if len({str(item).lower() for item in value}) != len(value):
            raise serializers.ValidationError("retained_image_ids must not repeat.")
        return value

    def validate_main_image_id(self, value):
        if value in (None, ""):
            return value
        if not is_uuid(value):
            raise serializers.ValidationError("main_image_id must be an image UUID.")
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
        if not isinstance(value, list) or len(value) > LISTING_IMAGE_CAP:
            raise serializers.ValidationError("images_metadata must be a list.")
        seen = set()
        for item in value:
            if not isinstance(item, dict) or "id" not in item:
                raise serializers.ValidationError(
                    "Each item in images_metadata must be an object with an 'id' field."
                )
            if not is_uuid(item["id"]):
                raise serializers.ValidationError("images_metadata ids must be UUIDs.")
            if str(item["id"]).lower() in seen:
                raise serializers.ValidationError("images_metadata ids must not repeat.")
            seen.add(str(item["id"]).lower())
            for key, limit in (("name", 255), ("description", 4000)):
                text = item.get(key)
                if text is not None and (not isinstance(text, str) or len(text) > limit):
                    raise serializers.ValidationError(
                        f"images_metadata {key} must be text of at most {limit} characters."
                    )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        from core_apps.properties.catalog_access import validate_property_locations

        validate_property_locations(attrs, self.instance)
        city = attrs.get("city", getattr(self.instance, "city", None))
        governorate = attrs.get(
            "governorate", getattr(self.instance, "governorate", None)
        )
        if city and governorate and city.governorate_id != governorate.pkid:
            raise serializers.ValidationError(
                {"city": "The selected city does not belong to this governorate."}
            )
        district = attrs.get(
            "district_catalog", getattr(self.instance, "district_catalog", None)
        )
        if district and (not city or district.city_id != city.pk):
            raise serializers.ValidationError(
                {"district_catalog": "Choose a district in the selected city."}
            )
        if "district_catalog" in attrs and district:
            attrs["district"] = district.name
        if not self.instance:
            # A2-06: edit-only image keys have defined create semantics. Empty
            # values are ignored (nothing to retain yet); anything else is 400
            # instead of reaching Property(**data).
            for key in ("main_image_id", "retained_image_ids", "images_metadata"):
                if key in attrs and attrs[key] not in (None, "", []):
                    raise serializers.ValidationError(
                        {key: "Only valid when editing an existing listing."}
                    )
                attrs.pop(key, None)
        if attrs.get("video") is not None:
            # The decoded duration is authoritative; the client value is a hint.
            attrs["video_duration"] = measured_seconds(attrs["video"].sukoon_duration_ms)
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
