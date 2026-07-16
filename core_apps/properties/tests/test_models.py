import pytest
from core_apps.properties.models import Property, PropertyImage


@pytest.mark.django_db
class TestPropertyModel:
    def test_create_property_defaults(self, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Apartment in Nasr City",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        assert property_obj.title == "Apartment in Nasr City"
        assert property_obj.price == 15000.00
        assert property_obj.price_period == Property.PricePeriod.MONTHLY
        assert property_obj.property_type == Property.PropertyType.APARTMENT
        assert not property_obj.is_furnished
        assert not property_obj.is_verified
        assert not property_obj.main_image
        assert property_obj.bedrooms == 1
        assert property_obj.bathrooms == 1
        assert property_obj.area == 0
        assert property_obj.space == ""
        assert property_obj.floor is None
        assert property_obj.rental_period == 1
        assert property_obj.suitable_for == Property.SuitableFor.ALL
        assert not property_obj.smoking_allowed
        assert property_obj.country == "Egypt"
        assert property_obj.city == "Cairo"
        assert property_obj.district == "Nasr City"
        assert str(property_obj) == "Apartment in Nasr City"

    def test_create_property_with_main_image(self, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Apartment in Nasr City",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
            main_image="properties/main_images/living_room.jpg",
            space="120m"
        )
        assert property_obj.main_image == "properties/main_images/living_room.jpg"
        assert property_obj.space == "120m"

    def test_create_property_image(self, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Apartment in Nasr City",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        image_obj = PropertyImage.objects.create(
            property=property_obj,
            image="properties/images/sample.jpg",
            name="Living Room",
            description="Spacious living room area."
        )
        assert image_obj.property == property_obj
        assert image_obj.image == "properties/images/sample.jpg"
        assert image_obj.name == "Living Room"
        assert image_obj.description == "Spacious living room area."
        assert str(image_obj) == f"Image for property: {property_obj.title}"
        assert property_obj.images.count() == 1

        # Check default values are blank strings
        blank_image = PropertyImage.objects.create(
            property=property_obj,
            image="properties/images/sample2.jpg"
        )
        assert blank_image.name == ""
        assert blank_image.description == ""

    def test_create_property_suitable_for_female_students(self, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Girls Housing",
            price=12000.00,
            city="Cairo",
            district="Nasr City",
            suitable_for=Property.SuitableFor.FEMALE_STUDENTS,
        )
        assert property_obj.suitable_for == Property.SuitableFor.FEMALE_STUDENTS
        assert property_obj.suitable_for == "female_students"
