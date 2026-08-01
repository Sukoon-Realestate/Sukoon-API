import pytest

from core_apps.properties.models import Property, PropertyImage, PropertyVisit
from core_apps.properties.services import PropertyService, PropertyVisitService


def _create_property(**kwargs):
    from core_apps.properties.models import PropertyType

    defaults = {
        "title": "Service Property",
        "price": 10000.00,
        "city": "Cairo",
        "district": "Maadi",
        "property_type": PropertyType.objects.get_or_create(
            slug="apartment", defaults={"name": "Apartment"}
        )[0],
    }
    defaults.update(kwargs)
    return Property.objects.create(**defaults)


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
            "property_type": None,
        }
        from core_apps.properties.models import PropertyType

        validated_data["property_type"] = PropertyType.objects.get_or_create(
            slug="apartment", defaults={"name": "Apartment"}
        )[0]
        property_obj = PropertyService.create_property(
            owner=user, validated_data=validated_data
        )
        assert property_obj.title == "Service Apartment"
        assert property_obj.owner == user
        assert Property.objects.filter(title="Service Apartment").count() == 1

    def test_update_property_service(self, user):
        property_obj = _create_property(owner=user, title="Old Title", price=8000.00)
        validated_data = {
            "title": "New Title",
            "price": 9500.00,
        }
        updated_obj = PropertyService.update_property(
            property_obj=property_obj, validated_data=validated_data
        )
        assert updated_obj.title == "New Title"
        assert updated_obj.price == 9500.00
        assert Property.objects.get(id=property_obj.id).title == "New Title"

    def test_upload_property_images_service(self, user):
        property_obj = _create_property(owner=user)
        uploaded_images = ["properties/images/living.jpg", "properties/images/bed.jpg"]
        images = PropertyService.upload_property_images(property_obj, uploaded_images)
        assert len(images) == 2
        assert images[0].property == property_obj
        assert images[0].image == "properties/images/living.jpg"
        assert property_obj.images.count() == 2

    def test_update_property_image_service(self, user):
        property_obj = _create_property(owner=user)
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


@pytest.mark.django_db
class TestPropertyVisitService:
    from rest_framework.exceptions import PermissionDenied, ValidationError

    def test_create_visit_service_success(self, user, another_user):
        property_obj = _create_property(owner=user, title="Sample Property")
        validated_data = {
            "visit_date": "2026-07-20",
            "visit_time": "14:00:00",
            "note": "Let's visit",
        }
        visit = PropertyVisitService.create_visit(
            tenant=another_user, property_obj=property_obj, validated_data=validated_data
        )
        assert visit.tenant == another_user
        assert visit.property == property_obj
        assert visit.status == PropertyVisit.Status.PENDING

    def test_create_visit_service_owner_cannot_book(self, user):
        property_obj = _create_property(owner=user, title="Sample Property")
        validated_data = {
            "visit_date": "2026-07-20",
            "visit_time": "14:00:00",
        }
        from rest_framework.exceptions import ValidationError

        with pytest.raises(ValidationError) as excinfo:
            PropertyVisitService.create_visit(
                tenant=user, property_obj=property_obj, validated_data=validated_data
            )
        assert "You cannot book a visit for your own property." in str(excinfo.value)

    def test_create_visit_service_duplicate_fails(self, user, another_user):
        property_obj = _create_property(owner=user, title="Sample Property")
        validated_data = {
            "visit_date": "2026-07-20",
            "visit_time": "14:00:00",
        }
        PropertyVisitService.create_visit(
            tenant=another_user, property_obj=property_obj, validated_data=validated_data
        )
        from rest_framework.exceptions import ValidationError

        with pytest.raises(ValidationError) as excinfo:
            PropertyVisitService.create_visit(
                tenant=another_user, property_obj=property_obj, validated_data=validated_data
            )
        assert "You have already requested a visit for this property" in str(excinfo.value)

    def test_update_visit_status_tenant_cancels(self, user, another_user):
        property_obj = _create_property(owner=user, title="Sample Property")
        visit = PropertyVisit.objects.create(
            property=property_obj,
            tenant=another_user,
            visit_date="2026-07-20",
            visit_time="14:00:00",
        )
        updated_visit = PropertyVisitService.update_visit_status(
            user=another_user, visit_obj=visit, status=PropertyVisit.Status.CANCELED
        )
        assert updated_visit.status == PropertyVisit.Status.CANCELED

    def test_update_visit_status_owner_confirms_and_rejects(self, user, another_user):
        property_obj = _create_property(owner=user, title="Sample Property")
        visit = PropertyVisit.objects.create(
            property=property_obj,
            tenant=another_user,
            visit_date="2026-07-20",
            visit_time="14:00:00",
        )
        updated_visit = PropertyVisitService.update_visit_status(
            user=user, visit_obj=visit, status=PropertyVisit.Status.CONFIRMED
        )
        assert updated_visit.status == PropertyVisit.Status.CONFIRMED

        from rest_framework.exceptions import ValidationError

        with pytest.raises(ValidationError):
            PropertyVisitService.update_visit_status(
                user=user, visit_obj=updated_visit, status=PropertyVisit.Status.REJECTED
            )

    def test_update_visit_status_unauthorized_user(self, user, another_user, superuser):
        property_obj = _create_property(owner=user, title="Sample Property")
        visit = PropertyVisit.objects.create(
            property=property_obj,
            tenant=another_user,
            visit_date="2026-07-20",
            visit_time="14:00:00",
        )
        from rest_framework.exceptions import PermissionDenied

        with pytest.raises(PermissionDenied):
            PropertyVisitService.update_visit_status(
                user=superuser, visit_obj=visit, status=PropertyVisit.Status.CANCELED
            )
        with pytest.raises(PermissionDenied):
            PropertyVisitService.update_visit_status(
                user=superuser, visit_obj=visit, status=PropertyVisit.Status.CONFIRMED
            )
