import pytest

from core_apps.properties.models import Property, PropertyImage
from core_apps.properties.services import PropertyService


@pytest.mark.django_db
class TestPropertyService:
    def test_create_property_service(self, user):
        validated_data = {
            "title": "Service Apartment",
            "price": 10000.00,
            "city": "Cairo",
            "district": "Maadi",
            "bedrooms": 2,
            "bathrooms": 1,
            "area": 85,
        }
        # Call service directly
        property_obj = PropertyService.create_property(
            owner=user, validated_data=validated_data
        )
        assert property_obj.title == "Service Apartment"
        assert property_obj.owner == user
        assert Property.objects.filter(title="Service Apartment").count() == 1

    def test_update_property_service(self, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Old Title",
            price=8000.00,
            city="Cairo",
            district="Maadi",
        )
        validated_data = {
            "title": "New Title",
            "price": 9500.00,
        }
        # Call service directly
        updated_obj = PropertyService.update_property(
            property_obj=property_obj, validated_data=validated_data
        )
        assert updated_obj.title == "New Title"
        assert updated_obj.price == 9500.00
        assert Property.objects.get(id=property_obj.id).title == "New Title"

    def test_upload_property_images_service(self, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Service Property",
            price=10000.00,
            city="Cairo",
            district="Maadi",
        )
        uploaded_images = ["properties/images/living.jpg", "properties/images/bed.jpg"]
        images = PropertyService.upload_property_images(property_obj, uploaded_images)
        assert len(images) == 2
        assert images[0].property == property_obj
        assert images[0].image == "properties/images/living.jpg"
        assert property_obj.images.count() == 2

    def test_update_property_image_service(self, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Service Property",
            price=10000.00,
            city="Cairo",
            district="Maadi",
        )
        image_obj = PropertyImage.objects.create(
            property=property_obj,
            image="properties/images/living.jpg",
            name="Old Name",
        )
        updated_image = PropertyService.update_property_image(
            image_obj=image_obj,
            validated_data={"name": "New Name", "description": "Beautiful room"},
        )
        assert updated_image.name == "New Name"
        assert updated_image.description == "Beautiful room"
