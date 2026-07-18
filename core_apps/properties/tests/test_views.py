import io
import uuid
from PIL import Image
from unittest.mock import patch

import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status

from core_apps.common.models import ContentView
from core_apps.properties.models import Property, PropertyImage, PropertyVisit


@pytest.fixture(autouse=True)
def mock_cloudinary_upload():
    mock_upload_response = lambda file, **kwargs: {
        "public_id": f"mocked_{file.name}" if hasattr(file, "name") else "mocked_file",
        "url": (
            f"https://res.cloudinary.com/mocked/{file.name}"
            if hasattr(file, "name")
            else "https://res.cloudinary.com/mocked/file"
        ),
        "secure_url": (
            f"https://res.cloudinary.com/mocked/{file.name}"
            if hasattr(file, "name")
            else "https://res.cloudinary.com/mocked/file"
        ),
        "format": "png",
        "resource_type": "image",
        "version": 123456,
        "type": "upload",
    }
    with patch(
        "cloudinary.uploader.upload", side_effect=mock_upload_response
    ) as mocked:
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

    def test_retrieve_property_records_authenticated_view(self, api_client, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Apartment in Nasr City",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        api_client.force_authenticate(user=user)
        url = reverse("property-detail", kwargs={"id": property_obj.id})

        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        content_type = ContentType.objects.get_for_model(Property)
        views = ContentView.objects.filter(
            content_type=content_type, object_id=property_obj.pkid, user=user
        )
        assert views.count() == 1

        # A repeat view by the same user refreshes the row instead of duplicating it
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert views.count() == 1

    def test_retrieve_property_records_anonymous_view(self, api_client, user):
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

        content_type = ContentType.objects.get_for_model(Property)
        assert ContentView.objects.filter(
            content_type=content_type, object_id=property_obj.pkid, user=None
        ).exists()

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


@pytest.mark.django_db
class TestMyPropertyListView:
    def test_my_properties_unauthenticated_returns_401(self, api_client):
        url = reverse("my-property-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_my_properties_happy_path_with_counts(
        self, auth_client, user, another_user
    ):
        property_obj = Property.objects.create(
            owner=user,
            title="My Apartment",
            price=15000.00,
            city="Cairo",
            district="Nasr City",
        )
        # Another owner's property must not appear in the response
        Property.objects.create(
            owner=another_user,
            title="Not Mine",
            price=9000.00,
            city="Cairo",
            district="Heliopolis",
        )
        PropertyVisit.objects.create(
            property=property_obj,
            tenant=another_user,
            visit_date="2026-07-20",
            visit_time="14:00:00",
        )
        content_type = ContentType.objects.get_for_model(Property)
        ContentView.objects.create(
            content_type=content_type,
            object_id=property_obj.pkid,
            user=another_user,
            viewer_ip="127.0.0.1",
            last_viewed=timezone.now(),
        )
        ContentView.objects.create(
            content_type=content_type,
            object_id=property_obj.pkid,
            user=None,
            viewer_ip="10.0.0.1",
            last_viewed=timezone.now(),
        )

        url = reverse("my-property-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        item = response.data["results"][0]
        assert item["title"] == "My Apartment"
        assert "main_image" in item
        assert item["price"] == "15000.00"
        assert item["status"] == Property.Status.UNDER_REVIEW
        assert item["views_count"] == 2
        assert item["visits_count"] == 1

        json_data = response.json()
        assert json_data["status_code"] == 200
        assert "properties" in json_data

    def test_my_properties_queries_optimized(self, auth_client, user, another_user):
        for i in range(5):
            property_obj = Property.objects.create(
                owner=user,
                title=f"Apartment {i}",
                price=15000.00,
                city="Cairo",
                district="Nasr City",
            )
            PropertyVisit.objects.create(
                property=property_obj,
                tenant=another_user,
                visit_date="2026-07-20",
                visit_time="14:00:00",
            )
        url = reverse("my-property-list")

        with CaptureQueriesContext(connection) as ctx:
            response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5
        # Pagination count + annotated list query (+ one-time ContentType lookup)
        assert len(ctx.captured_queries) <= 3

    def test_owner_cannot_set_status_via_api(self, auth_client):
        url = reverse("property-create")
        data = {
            "title": "Apartment in Heliopolis",
            "price": 20000.00,
            "city": "Cairo",
            "district": "Heliopolis",
            "status": Property.Status.VERIFIED,
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        property_obj = Property.objects.get(title="Apartment in Heliopolis")
        assert property_obj.status == Property.Status.UNDER_REVIEW


@pytest.mark.django_db
class TestPropertyVisitViews:
    def test_create_visit_unauthenticated_returns_401(self, api_client, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Apartment Heliopolis",
            price=20000.00,
            city="Cairo",
            district="Heliopolis",
        )
        url = reverse("property-visit-create", kwargs={"property_id": property_obj.id})
        data = {
            "visit_date": "2026-07-20",
            "visit_time": "14:00:00",
            "note": "Can I view it?",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_visit_authenticated_happy_path(
        self, auth_client, user, another_user
    ):
        property_obj = Property.objects.create(
            owner=user,
            title="Apartment Heliopolis",
            price=20000.00,
            city="Cairo",
            district="Heliopolis",
        )
        # Auth client uses "user" fixture as authenticated user. So let's make another_user the owner to let "user" book.
        property_obj.owner = another_user
        property_obj.save()

        url = reverse("property-visit-create", kwargs={"property_id": property_obj.id})
        data = {
            "visit_date": "2026-07-20",
            "visit_time": "14:00:00",
            "note": "Can I view it?",
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert PropertyVisit.objects.filter(property=property_obj, tenant=user).exists()

    def test_create_visit_owner_cannot_book_own_property(self, auth_client, user):
        property_obj = Property.objects.create(
            owner=user,
            title="Apartment Heliopolis",
            price=20000.00,
            city="Cairo",
            district="Heliopolis",
        )
        url = reverse("property-visit-create", kwargs={"property_id": property_obj.id})
        data = {
            "visit_date": "2026-07-20",
            "visit_time": "14:00:00",
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "You cannot book a visit for your own property." in str(response.data)

    def test_list_tenant_visits(self, auth_client, user, another_user):
        property_obj = Property.objects.create(
            owner=another_user,
            title="Apartment Heliopolis",
            price=20000.00,
            city="Cairo",
            district="Heliopolis",
        )
        visit1 = PropertyVisit.objects.create(
            property=property_obj,
            tenant=user,
            visit_date="2026-07-20",
            visit_time="14:00:00",
        )
        url = reverse("tenant-visit-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        assert "visits" in json_data
        assert len(json_data["visits"]["results"]) == 1
        assert json_data["visits"]["results"][0]["tenant_email"] == user.email

    def test_list_owner_received_visits(self, auth_client, user, another_user):
        property_obj = Property.objects.create(
            owner=user,
            title="Owner Property",
            price=20000.00,
            city="Cairo",
            district="Heliopolis",
        )
        visit1 = PropertyVisit.objects.create(
            property=property_obj,
            tenant=another_user,
            visit_date="2026-07-20",
            visit_time="14:00:00",
            status=PropertyVisit.Status.PENDING,
        )
        url = reverse("owner-visit-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        assert "visits" in json_data
        assert len(json_data["visits"]["results"]) == 1
        # Owner received list returns the trimmed visit payload
        result = json_data["visits"]["results"][0]
        assert set(result.keys()) == {"tenant", "visit_date", "status"}
        assert set(result["tenant"].keys()) == {"name", "avatar", "is_verified"}
        assert result["tenant"]["name"] == another_user.get_full_name

    def test_list_tenant_visits_filter_by_status(self, auth_client, user, another_user):
        property_obj = Property.objects.create(
            owner=another_user,
            title="Apartment Heliopolis",
            price=20000.00,
            city="Cairo",
            district="Heliopolis",
        )
        PropertyVisit.objects.create(
            property=property_obj,
            tenant=user,
            visit_date="2026-07-20",
            visit_time="14:00:00",
            status=PropertyVisit.Status.PENDING,
        )
        PropertyVisit.objects.create(
            property=property_obj,
            tenant=user,
            visit_date="2026-07-21",
            visit_time="15:00:00",
            status=PropertyVisit.Status.CONFIRMED,
        )
        url = reverse("tenant-visit-list")
        response = auth_client.get(url, {"status": "confirmed"})

        assert response.status_code == status.HTTP_200_OK
        results = response.json()["visits"]["results"]
        assert len(results) == 1
        assert results[0]["status"] == PropertyVisit.Status.CONFIRMED

    def test_list_tenant_visits_invalid_status_returns_400(self, auth_client):
        url = reverse("tenant-visit-list")
        response = auth_client.get(url, {"status": "not-a-status"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_owner_received_visits_filter_by_status(
        self, auth_client, user, another_user
    ):
        property_obj = Property.objects.create(
            owner=user,
            title="Owner Property",
            price=20000.00,
            city="Cairo",
            district="Heliopolis",
        )
        PropertyVisit.objects.create(
            property=property_obj,
            tenant=another_user,
            visit_date="2026-07-20",
            visit_time="14:00:00",
            status=PropertyVisit.Status.PENDING,
        )
        PropertyVisit.objects.create(
            property=property_obj,
            tenant=another_user,
            visit_date="2026-07-21",
            visit_time="15:00:00",
            status=PropertyVisit.Status.REJECTED,
        )
        url = reverse("owner-visit-list")
        response = auth_client.get(url, {"status": "pending"})

        assert response.status_code == status.HTTP_200_OK
        results = response.json()["visits"]["results"]
        assert len(results) == 1
        assert results[0]["status"] == PropertyVisit.Status.PENDING

    def test_owner_confirms_visit_and_received_list_stays_trimmed(
        self, auth_client, user, another_user
    ):
        property_obj = Property.objects.create(
            owner=user,
            title="Owner Property",
            price=20000.00,
            city="Cairo",
            district="Heliopolis",
        )
        visit = PropertyVisit.objects.create(
            property=property_obj,
            tenant=another_user,
            visit_date="2026-07-20",
            visit_time="14:00:00",
            status=PropertyVisit.Status.PENDING,
        )
        url = reverse("property-visit-update", kwargs={"id": visit.id})
        response = auth_client.patch(url, {"status": "confirmed"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        visit.refresh_from_db()
        assert visit.status == PropertyVisit.Status.CONFIRMED

        # ? Owner received list is always trimmed — tenant email is never exposed,
        # ? even after the visit is confirmed
        list_url = reverse("owner-visit-list")
        list_response = auth_client.get(list_url)
        assert list_response.status_code == status.HTTP_200_OK
        results = list_response.json()["visits"]["results"]
        assert set(results[0].keys()) == {"tenant", "visit_date", "status"}
        assert results[0]["status"] == PropertyVisit.Status.CONFIRMED

    def test_retrieve_visit_detail_returns_trimmed_payload(
        self, auth_client, user, another_user
    ):
        property_obj = Property.objects.create(
            owner=user,
            title="Owner Property",
            price=20000.00,
            city="Cairo",
            district="Heliopolis",
        )
        another_user.is_verified = True
        another_user.save()
        visit = PropertyVisit.objects.create(
            property=property_obj,
            tenant=another_user,
            visit_date="2026-07-20",
            visit_time="14:00:00",
        )
        url = reverse("property-visit-detail", kwargs={"id": visit.id})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        visit_data = response.json()["visit"]
        # ? Detail payload is intentionally trimmed to these keys only
        assert set(visit_data.keys()) == {"tenant", "visit_date", "status"}
        tenant_data = visit_data["tenant"]
        assert set(tenant_data.keys()) == {"name", "avatar", "is_verified"}
        assert tenant_data["name"] == another_user.get_full_name
        assert tenant_data["avatar"] is None
        assert tenant_data["is_verified"] is True
        assert visit_data["visit_date"] == "2026-07-20"
        assert visit_data["status"] == PropertyVisit.Status.PENDING

    def test_retrieve_visit_detail_unauthenticated_returns_401(
        self, api_client, user, another_user
    ):
        property_obj = Property.objects.create(
            owner=user,
            title="Owner Property",
            price=20000.00,
            city="Cairo",
            district="Heliopolis",
        )
        visit = PropertyVisit.objects.create(
            property=property_obj,
            tenant=another_user,
            visit_date="2026-07-20",
            visit_time="14:00:00",
        )
        url = reverse("property-visit-detail", kwargs={"id": visit.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_visit_detail_not_found_returns_404(self, auth_client):
        url = reverse("property-visit-detail", kwargs={"id": uuid.uuid4()})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_tenant_cancels_visit(self, auth_client, user, another_user):
        property_obj = Property.objects.create(
            owner=another_user,
            title="Other Property",
            price=20000.00,
            city="Cairo",
            district="Heliopolis",
        )
        visit = PropertyVisit.objects.create(
            property=property_obj,
            tenant=user,
            visit_date="2026-07-20",
            visit_time="14:00:00",
            status=PropertyVisit.Status.PENDING,
        )
        url = reverse("property-visit-update", kwargs={"id": visit.id})
        response = auth_client.patch(url, {"status": "canceled"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        visit.refresh_from_db()
        assert visit.status == PropertyVisit.Status.CANCELED
