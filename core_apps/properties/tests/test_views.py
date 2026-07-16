import io
import uuid
from PIL import Image
from unittest.mock import patch

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status

from core_apps.properties.models import Property, PropertyImage


@pytest.fixture(autouse=True)
def mock_cloudinary_upload():
    mock_upload_response = lambda file, **kwargs: {
        "public_id": f"mocked_{file.name}" if hasattr(file, "name") else "mocked_file",
        "url": f"https://res.cloudinary.com/mocked/{file.name}" if hasattr(file, "name") else "https://res.cloudinary.com/mocked/file",
        "secure_url": f"https://res.cloudinary.com/mocked/{file.name}" if hasattr(file, "name") else "https://res.cloudinary.com/mocked/file",
        "format": "png",
        "resource_type": "image",
        "version": 123456,
        "type": "upload",
    }
    with patch("cloudinary.uploader.upload", side_effect=mock_upload_response) as mocked:
        yield mocked


def generate_test_image():
    file = io.BytesIO()
    image = Image.new("RGBA", size=(100, 100), color=(155, 0, 0))
    image.save(file, "png")
    file.name = "test.png"
    file.seek(0)
    return SimpleUploadedFile(file.name, file.read(), content_type="image/png")


@pytest.mark.django_db
class TestPropertyViews:
    def test_list_properties_public_and_queries_optimized(self, auth_client, user):
        # Create multiple test properties to test N+1 query prevention
        for i in range(5):
            prop = Property.objects.create(
                owner=user,
                title=f"Apartment {i}",
                price=15000.00,
                city="Cairo",
                district="Nasr City",
            )
            if i == 0:
                PropertyImage.objects.create(property=prop, image="test1.png")
                PropertyImage.objects.create(property=prop, image="test2.png")
        url = reverse("property-list")

        # Capture query count to verify prefetch and select related are working
        with CaptureQueriesContext(connection) as ctx:
            response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Check raw response data
        assert "results" in response.data
        assert len(response.data["results"]) == 5

        # Verify that requested fields are excluded from list response payload
        first_item = response.data["results"][0]
        assert "owner" not in first_item
        assert "images" not in first_item
        assert "floor" not in first_item
        assert "area" not in first_item
        assert "latitude" not in first_item
        assert "longitude" not in first_item
        assert first_item["images_count"] == 0
        assert response.data["results"][4]["images_count"] == 2

        # Check rendered response JSON
        json_data = response.json()
        assert json_data["status_code"] == 200
        assert "properties" in json_data

        # Verify query count is small and constant (e.g. <= 3 queries)
        assert len(ctx.captured_queries) <= 3

    def test_create_property_unauthenticated_returns_401(self, api_client):
        url = reverse("property-create")
        data = {
            "title": "Apartment in Heliopolis",
            "price": 20000.00,
            "city": "Cairo",
            "district": "Heliopolis",
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_property_authenticated_happy_path(self, auth_client, user):
        url = reverse("property-create")
        data = {
            "title": "Apartment in Heliopolis",
            "price": 20000.00,
            "city": "Cairo",
            "district": "Heliopolis",
            "bedrooms": 2,
            "bathrooms": 2,
            "area": 120,
            "is_furnished": True,
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

        # Verify response.data
        assert response.data["title"] == "Apartment in Heliopolis"
        assert response.data["owner"] == user.get_full_name

        # Verify rendered JSON
        json_data = response.json()
        assert json_data["status_code"] == 201
        assert json_data["properties"]["title"] == "Apartment in Heliopolis"

    def test_create_property_invalid_payload_returns_400(self, auth_client):
        url = reverse("property-create")
        # Missing price and city
        data = {
            "title": "Apartment in Heliopolis",
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_property_happy_path(self, api_client, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Apartment in Nasr City",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        url = reverse("property-detail", kwargs={"id": property_obj.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Apartment in Nasr City"

    def test_retrieve_property_not_found_returns_404(self, api_client):
        url = reverse("property-detail", kwargs={"id": uuid.uuid4()})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_property_owner_happy_path(self, auth_client, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Apartment in Nasr City",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        url = reverse("property-update", kwargs={"id": property_obj.id})
        data = {"title": "Updated Apartment Title"}
        response = auth_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated Apartment Title"

    def test_update_property_unauthenticated_returns_401(self, api_client, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Apartment in Nasr City",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        url = reverse("property-update", kwargs={"id": property_obj.id})
        data = {"title": "Updated Apartment Title"}
        response = api_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_property_non_owner_returns_403(
        self, api_client, another_user, user
    ):
        property_obj = Property.objects.create(
            owner=user,
            title="Apartment in Nasr City",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        # Authenticate as another user
        api_client.force_authenticate(user=another_user)
        url = reverse("property-update", kwargs={"id": property_obj.id})
        data = {"title": "Updated Apartment Title"}
        response = api_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_property_not_found_returns_404(self, auth_client):
        url = reverse("property-update", kwargs={"id": uuid.uuid4()})
        data = {"title": "Updated Title"}
        response = auth_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_property_owner_happy_path(self, auth_client, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Apartment in Nasr City",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        url = reverse("property-delete", kwargs={"id": property_obj.id})
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Property.objects.filter(id=property_obj.id).exists()

    def test_delete_property_unauthenticated_returns_401(self, api_client, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Apartment in Nasr City",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        url = reverse("property-delete", kwargs={"id": property_obj.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_property_not_found_returns_404(self, auth_client):
        url = reverse("property-delete", kwargs={"id": uuid.uuid4()})
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_upload_property_images_happy_path(self, auth_client, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Upload Property",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        url = reverse("property-image-upload", kwargs={"property_id": property_obj.id})
        data = {
            "image": generate_test_image(),
            "name": "Living Room View",
            "description": "Lovely room view",
        }
        response = auth_client.post(url, data, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Living Room View"
        assert response.data["description"] == "Lovely room view"
        assert PropertyImage.objects.filter(property=property_obj).count() == 1

    def test_upload_property_images_not_owner(self, auth_client, another_user):
        other_user = another_user
        property_obj = Property.objects.create(
            owner=other_user,
            title="Upload Property",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        url = reverse("property-image-upload", kwargs={"property_id": property_obj.id})
        data = {
            "image": generate_test_image(),
            "name": "Living Room View",
            "description": "Lovely room view",
        }
        response = auth_client.post(url, data, format="multipart")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_property_image_metadata(self, auth_client, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Update Image Prop",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        image_obj = PropertyImage.objects.create(
            property=property_obj,
            image="properties/images/test.png",
            name="Living Room",
        )
        url = reverse("property-image-detail", kwargs={"id": image_obj.id})
        data = {"name": "Updated Room Name", "description": "Lovely room"}
        response = auth_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        image_obj.refresh_from_db()
        assert image_obj.name == "Updated Room Name"
        assert image_obj.description == "Lovely room"

    def test_update_property_image_not_owner(self, auth_client, another_user):
        other_user = another_user
        property_obj = Property.objects.create(
            owner=other_user,
            title="Update Image Prop",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        image_obj = PropertyImage.objects.create(
            property=property_obj,
            image="properties/images/test.png",
            name="Living Room",
        )
        url = reverse("property-image-detail", kwargs={"id": image_obj.id})
        data = {"name": "Hacked Room Name"}
        response = auth_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_property_image(self, auth_client, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Delete Image Prop",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        image_obj = PropertyImage.objects.create(
            property=property_obj,
            image="properties/images/test.png",
        )
        url = reverse("property-image-detail", kwargs={"id": image_obj.id})
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not PropertyImage.objects.filter(id=image_obj.id).exists()
