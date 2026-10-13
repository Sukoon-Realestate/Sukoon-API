"""PropertyCreation operations owned by PropertyService."""

from decimal import Decimal
from django.db import transaction
from ...models import Property, PropertyImage


class PropertyCreationMixin:
    @classmethod
    def _apply_rental_projection(cls, data):
        inventory = data.get("rental_inventory")
        if inventory is None:
            return
        eligible = [
            offer
            for offer in inventory.get("offers", [])
            if not offer.get("archived") and offer.get("availability") == "available"
        ]
        scopes = sorted(
            {
                offer.get("rental_scope")
                for offer in eligible
                if offer.get("rental_scope")
            }
        )
        data["rental_scopes"] = "," + ",".join(scopes) + "," if scopes else ""
        periods = {offer.get("terms", {}).get("price_period") for offer in eligible}
        if len(periods) == 1:
            period = periods.pop()
            prices = [Decimal(str(offer["terms"]["price"])) for offer in eligible]
            data["rental_price_period"] = period
            data["rental_min_price"] = min(prices) if prices else None
        else:
            data["rental_price_period"] = ""
            data["rental_min_price"] = None

    @classmethod
    @transaction.atomic
    def create_property(cls, owner, validated_data):
        """
        Creates a property listing conforming to the mobile handoff specification.
        """
        from rest_framework.exceptions import ValidationError

        data = validated_data.copy()
        cls._apply_rental_projection(data)
        main_image_file = data.pop("main_image", None)
        main_image_name = (data.pop("main_image_name", "") or "").strip()
        main_image_description = (data.pop("main_image_description", "") or "").strip()
        amenities = data.pop("amenities", None)

        # Distinguish street and district; fallback district to street on POST if district is empty
        street = (data.get("street") or "").strip()
        district = (data.get("district") or "").strip()
        if not district and street:
            data["district"] = street

        # Map amenities array to model booleans if provided
        if amenities is not None:
            for (
                amenity_val,
                field_name,
            ) in cls.SUPPORTED_AMENITIES_MAP.items():
                data[field_name] = amenity_val in amenities

        # Check conflicting video / ownership proof clear flags
        remove_video = data.pop("remove_video", False)
        if remove_video and data.get("video"):
            raise ValidationError(
                {
                    "video": "Cannot upload video and specify remove_video simultaneously."
                }
            )

        remove_ownership_proof = data.pop("remove_ownership_proof", False)
        if remove_ownership_proof and data.get("ownership_proof"):
            raise ValidationError(
                {
                    "ownership_proof": "Cannot upload ownership proof and specify remove_ownership_proof simultaneously."
                }
            )

        # Edits / creations always submit for review
        data["status"] = Property.Status.UNDER_REVIEW
        data["is_verified"] = False
        data["is_ownership_verified"] = False

        if main_image_file:
            data["main_image"] = main_image_file

        property_obj = Property.objects.create(owner=owner, **data)

        # If a cover image was uploaded, persist it as a stable PropertyImage
        if main_image_file:
            PropertyImage.objects.create(
                property=property_obj,
                image=property_obj.main_image,
                name=main_image_name,
                description=main_image_description,
            )

        return property_obj
