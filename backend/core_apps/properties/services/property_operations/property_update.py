"""PropertyUpdate operations owned by PropertyService."""

from django.db import transaction
from ...models import Property, PropertyImage


class PropertyUpdateMixin:
    @classmethod
    @transaction.atomic
    def update_property(cls, property_obj, validated_data):
        """
        Updates a property listing conforming to the mobile handoff specification.
        """
        from rest_framework.exceptions import ValidationError

        data = validated_data.copy()
        cls._apply_rental_projection(data)

        # Handle video removal and replacement conflict
        remove_video = data.pop("remove_video", False)
        new_video = data.get("video")
        if remove_video and new_video:
            raise ValidationError(
                {
                    "video": "Cannot upload video and specify remove_video simultaneously."
                }
            )
        if remove_video:
            property_obj.video = None
            property_obj.video_duration = None
            data.pop("video", None)
            data.pop("video_duration", None)

        # Handle ownership proof removal and replacement conflict
        remove_ownership_proof = data.pop("remove_ownership_proof", False)
        new_ownership_proof = data.get("ownership_proof")
        if remove_ownership_proof and new_ownership_proof:
            raise ValidationError(
                {
                    "ownership_proof": "Cannot upload ownership proof and specify remove_ownership_proof simultaneously."
                }
            )
        if remove_ownership_proof:
            property_obj.ownership_proof = None
            property_obj.is_ownership_verified = False
            data.pop("ownership_proof", None)
        elif new_ownership_proof:
            property_obj.is_ownership_verified = False

        # Image retention and metadata updates
        retained_image_ids = data.pop("retained_image_ids", None)
        images_metadata = data.pop("images_metadata", None)
        main_image_id = data.pop("main_image_id", None)
        main_image_file = data.pop("main_image", None)
        main_image_name = data.pop("main_image_name", None)
        main_image_description = data.pop("main_image_description", None)

        # 1. Retained image IDs: remove existing image records not listed
        if retained_image_ids is not None:
            retained_str_ids = [str(i) for i in retained_image_ids]
            current_images = list(property_obj.images.all())
            current_ids = {str(img.id): img for img in current_images}

            for rid in retained_str_ids:
                if rid not in current_ids:
                    raise ValidationError(
                        {
                            "retained_image_ids": f"Image with ID {rid} does not belong to this property."
                        }
                    )

            # Delete unlisted images
            for img_id, img_obj in current_ids.items():
                if img_id not in retained_str_ids:
                    img_obj.delete()

        # 2. Apply images_metadata by image ID
        if images_metadata is not None:
            current_images = {str(img.id): img for img in property_obj.images.all()}
            for meta in images_metadata:
                mid = str(meta.get("id"))
                if mid in current_images:
                    target_img = current_images[mid]
                    if "name" in meta:
                        target_img.name = (meta["name"] or "").strip()
                    if "description" in meta:
                        target_img.description = (meta["description"] or "").strip()
                    target_img.save()

        # 3. Handle cover photo replacement / selection
        if main_image_file:
            new_name = (
                (main_image_name or "").strip() if main_image_name is not None else ""
            )
            new_desc = (
                (main_image_description or "").strip()
                if main_image_description is not None
                else ""
            )
            created_cover = PropertyImage.objects.create(
                property=property_obj,
                image=main_image_file,
                name=new_name,
                description=new_desc,
            )
            property_obj.main_image = created_cover.image
        elif main_image_id:
            try:
                selected_cover = property_obj.images.get(id=main_image_id)
            except PropertyImage.DoesNotExist:
                raise ValidationError(
                    {
                        "main_image_id": "Selected cover image does not belong to this property."
                    }
                )
            property_obj.main_image = selected_cover.image
            if main_image_name is not None:
                selected_cover.name = (main_image_name or "").strip()
            if main_image_description is not None:
                selected_cover.description = (main_image_description or "").strip()
            selected_cover.save()
        else:
            # If cover captions were passed without image replacement
            if main_image_name is not None or main_image_description is not None:
                cover_img = property_obj.images.first()
                if cover_img:
                    if main_image_name is not None:
                        cover_img.name = (main_image_name or "").strip()
                    if main_image_description is not None:
                        cover_img.description = (main_image_description or "").strip()
                    cover_img.save()

        # Map amenities array if provided
        amenities = data.pop("amenities", None)
        if amenities is not None:
            for (
                amenity_val,
                field_name,
            ) in cls.SUPPORTED_AMENITIES_MAP.items():
                data[field_name] = amenity_val in amenities

        # Apply scalar updates
        for attr, value in data.items():
            setattr(property_obj, attr, value)

        # On every owner edit, set status to under_review
        property_obj.status = Property.Status.UNDER_REVIEW
        property_obj.save()
        if hasattr(property_obj, "_prefetched_objects_cache"):
            property_obj._prefetched_objects_cache.clear()
        return property_obj
