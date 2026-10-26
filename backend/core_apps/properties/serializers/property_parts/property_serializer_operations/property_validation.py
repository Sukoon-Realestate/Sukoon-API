"""PropertyValidation operations owned by PropertySerializer."""

import json
from django.utils import timezone
from rest_framework import serializers
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
