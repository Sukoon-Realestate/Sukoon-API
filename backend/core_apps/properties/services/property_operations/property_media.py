"""PropertyMedia operations owned by PropertyService."""

from django.db import transaction
from ...models import Property, PropertyImage


class PropertyMediaMixin:
    @classmethod
    @transaction.atomic
    def upload_property_image(cls, property_obj, image, name="", description=""):
        """
        Uploads an image with transactional enforcement of the 25 images limit.
        """
        from rest_framework.exceptions import ValidationError

        locked_property = Property.objects.select_for_update().get(
            pkid=property_obj.pkid
        )
        if locked_property.images.count() >= 25:
            raise ValidationError(
                {"detail": "A property cannot have more than 25 images."}
            )

        name = (name or "").strip()
        description = (description or "").strip()

        img_obj = PropertyImage.objects.create(
            property=locked_property,
            image=image,
            name=name,
            description=description,
        )
        return img_obj

    @classmethod
    @transaction.atomic
    def upload_property_images(cls, property_obj, uploaded_images):
        """
        Uploads and creates multiple PropertyImage objects for a given property.
        """
        created_images = []
        for image in uploaded_images:
            img_obj = cls.upload_property_image(property_obj, image)
            created_images.append(img_obj)
        return created_images

    @classmethod
    @transaction.atomic
    def update_property_image(cls, image_obj, validated_data):
        """
        Updates metadata (name, description) of a PropertyImage.
        """
        for attr, value in validated_data.items():
            if attr in ("name", "description") and isinstance(value, str):
                value = value.strip()
            setattr(image_obj, attr, value)
        image_obj.save()
        return image_obj
