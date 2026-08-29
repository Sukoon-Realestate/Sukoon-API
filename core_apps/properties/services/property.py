from django.db import transaction
from django.db.models import Q

from ..models import Property, PropertyImage


class PropertyService:
    @staticmethod
    def get_available_places(property_type):
        """Return distinct locations for approved properties of a given type."""
        places = (
            Property.objects.filter(
                property_type=property_type,
            )
            .filter(Q(status=Property.Status.VERIFIED) | Q(is_verified=True))
            .values("governorate__name", "city__name", "district")
            .distinct()
            .order_by("governorate__name", "city__name", "district")
        )
        return [
            {
                "governorate": place["governorate__name"],
                "city": place["city__name"],
                "district": place["district"],
            }
            for place in places
        ]

    @staticmethod
    @transaction.atomic
    def create_property(owner, validated_data):
        """
        Creates a property listing.
        """
        return Property.objects.create(owner=owner, **validated_data)

    @staticmethod
    @transaction.atomic
    def update_property(property_obj, validated_data):
        """
        Updates a property listing.
        """
        for attr, value in validated_data.items():
            setattr(property_obj, attr, value)
        property_obj.save()
        return property_obj

    @staticmethod
    @transaction.atomic
    def upload_property_images(property_obj, uploaded_images):
        """
        Uploads and creates multiple PropertyImage objects for a given property.
        """
        created_images = []
        for image in uploaded_images:
            img_obj = PropertyImage.objects.create(property=property_obj, image=image)
            created_images.append(img_obj)
        return created_images

    @staticmethod
    @transaction.atomic
    def update_property_image(image_obj, validated_data):
        """
        Updates metadata (name, description) of a PropertyImage.
        """
        for attr, value in validated_data.items():
            setattr(image_obj, attr, value)
        image_obj.save()
        return image_obj
