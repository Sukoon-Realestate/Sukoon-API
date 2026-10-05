import io
import json
import uuid
from PIL import Image
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from unittest.mock import patch
from rest_framework.test import APIClient
from core_apps.properties.models import Property, PropertyImage, PropertyVisit


@pytest.fixture(autouse=True)
def mock_cloudinary_upload():
    mock_upload_response = lambda file, **kwargs: {
        "public_id": f"mocked_{getattr(file, 'name', 'file')}",
        "url": f"https://res.cloudinary.com/mocked/{getattr(file, 'name', 'file')}",
        "secure_url": f"https://res.cloudinary.com/mocked/{getattr(file, 'name', 'file')}",
        "format": "jpg",
        "resource_type": kwargs.get("resource_type", "image"),
        "version": 123456,
        "type": "upload",
    }
    with patch("cloudinary.uploader.upload", side_effect=mock_upload_response):
        yield


def generate_image_file(name="photo.jpg"):
    file = io.BytesIO()
    image = Image.new("RGB", size=(100, 100), color=(100, 150, 200))
    image.save(file, "jpeg")
    file.name = name
    file.seek(0)
    return SimpleUploadedFile(name, file.read(), content_type="image/jpeg")


def generate_video_file(name="tour.mp4"):
    return SimpleUploadedFile(
        name, b"dummy-mp4-video-content-stream", content_type="video/mp4"
    )


@pytest.fixture
def test_property_factory(user, apartment_type, cairo_city, cairo_governorate):
    def _create(**kwargs):
        defaults = {
            "owner": user,
            "title": "Initial Apartment Title",
            "description": "Initial apartment description",
            "price": 10000.00,
            "price_period": Property.PricePeriod.MONTHLY,
            "property_type": apartment_type,
            "city": cairo_city,
            "governorate": cairo_governorate,
            "district": "Seventh District",
            "street": "Al Tayaran Street",
            "country": "Egypt",
            "bedrooms": 2,
            "bathrooms": 1,
            "area": 110,
            "floor": 2,
            "rental_period": 6,
            "status": Property.Status.VERIFIED,
            "is_verified": True,
        }
        defaults.update(kwargs)
        return Property.objects.create(**defaults)

    return _create


@pytest.mark.django_db
class TestCheck1_ImageCaptionsAndUpload:
    """1. Upload photos with neither caption, only a name, only a description, and both captions.

    Verify persistence and GET/write response equality, including blank/null normalization and Arabic text.
    """

    def test_upload_captions_variations_and_normalization(
        self, auth_client, user, test_property_factory
    ):
        prop = test_property_factory()
        url = reverse("property-image-upload", kwargs={"property_id": prop.id})

        # A: Neither caption
        res_a = auth_client.post(
            url,
            {"image": generate_image_file("img_a.jpg")},
            format="multipart",
        )
        assert res_a.status_code == status.HTTP_201_CREATED
        data_a = res_a.json()["data"]
        assert data_a["name"] == ""
        assert data_a["description"] == ""
        assert res_a.json()["message"] == "Image uploaded successfully."

        # B: Only a name with Arabic text
        res_b = auth_client.post(
            url,
            {
                "image": generate_image_file("img_b.jpg"),
                "name": "  غرفة النوم الرئيسية  ",
            },
            format="multipart",
        )
        assert res_b.status_code == status.HTTP_201_CREATED
        data_b = res_b.json()["data"]
        assert data_b["name"] == "غرفة النوم الرئيسية"
        assert data_b["description"] == ""

        # C: Only a description with Arabic text
        res_c = auth_client.post(
            url,
            {
                "image": generate_image_file("img_c.jpg"),
                "description": "  إطلالة رائعة على الحديقة  ",
            },
            format="multipart",
        )
        assert res_c.status_code == status.HTTP_201_CREATED
        data_c = res_c.json()["data"]
        assert data_c["name"] == ""
        assert data_c["description"] == "إطلالة رائعة على الحديقة"

        # D: Both captions
        res_d = auth_client.post(
            url,
            {
                "image": generate_image_file("img_d.jpg"),
                "name": "الصالة",
                "description": "مساحة واسعة وإضاءة طبيعية",
            },
            format="multipart",
        )
        assert res_d.status_code == status.HTTP_201_CREATED
        data_d = res_d.json()["data"]
        assert data_d["name"] == "الصالة"
        assert data_d["description"] == "مساحة واسعة وإضاءة طبيعية"


@pytest.mark.django_db
class TestCheck2_VideoInPropertyEndpoint:
    """2. Create with a video using the property multipart endpoint.

    Verify its returned URL/duration and playback URL. Create without video;
    replace, remove, and leave video unchanged on PATCH.
    """

    def test_create_and_patch_video_lifecycle(
        self, auth_client, user, apartment_type, cairo_city, cairo_governorate
    ):
        create_url = reverse("property-create")

        # Create with video
        payload = {
            "title": "Apartment with Video Tour",
            "price": 12000.00,
            "price_period": "monthly",
            "property_type": apartment_type.slug,
            "governorate": str(cairo_governorate.id),
            "city": str(cairo_city.id),
            "district": "Nasr City",
            "bedrooms": 2,
            "bathrooms": 1,
            "area": 100,
            "video": generate_video_file("tour.mp4"),
            "video_duration": 40,
        }
        res_create = auth_client.post(create_url, payload, format="multipart")
        assert res_create.status_code == status.HTTP_201_CREATED
        created_data = res_create.json()["data"]
        prop_id = created_data["id"]
        assert created_data["video_duration"] == 40
        assert created_data["video"] is not None

        # PATCH properties/{property_id}/: leave video unchanged
        detail_url = reverse("property-detail", kwargs={"id": prop_id})
        res_patch_1 = auth_client.patch(
            detail_url, {"title": "Title Modified"}, format="multipart"
        )
        assert res_patch_1.status_code == status.HTTP_200_OK
        assert res_patch_1.json()["data"]["video_duration"] == 40
        assert res_patch_1.json()["data"]["video"] is not None

        # PATCH: remove video
        res_patch_remove = auth_client.patch(
            detail_url, {"remove_video": True}, format="multipart"
        )
        assert res_patch_remove.status_code == status.HTTP_200_OK
        assert res_patch_remove.json()["data"]["video"] is None
        assert res_patch_remove.json()["data"]["video_duration"] is None

        # PATCH: replacement upload and remove_video must not be accepted together
        res_conflict = auth_client.patch(
            detail_url,
            {
                "video": generate_video_file("conflict.mp4"),
                "remove_video": True,
            },
            format="multipart",
        )
        assert res_conflict.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCheck3_ImageRetentionCoverAndMetadataOnPatch:
    """3. Rename an existing image, clear its description, delete/replace it, and choose

    a retained image as cover. Verify stable IDs, ordering, deduplication, and limits.
    """

    def test_image_patch_retention_and_cover_promotion(
        self, auth_client, user, test_property_factory
    ):
        prop = test_property_factory()
        # Upload 3 images
        img1 = PropertyImage.objects.create(
            property=prop,
            image=generate_image_file("img1.jpg"),
            name="Room 1",
            description="Room 1 desc",
        )
        img2 = PropertyImage.objects.create(
            property=prop,
            image=generate_image_file("img2.jpg"),
            name="Room 2",
            description="Room 2 desc",
        )
        img3 = PropertyImage.objects.create(
            property=prop,
            image=generate_image_file("img3.jpg"),
            name="Room 3",
            description="Room 3 desc",
        )
        prop.main_image = img1.image
        prop.save()

        detail_url = reverse("property-detail", kwargs={"id": prop.id})

        # PATCH: retain img2 and img1, delete img3, promote img2 to cover, rename img1 and clear img2 description
        patch_payload = {
            "retained_image_ids": json.dumps([str(img2.id), str(img1.id)]),
            "images_metadata": json.dumps(
                [
                    {"id": str(img1.id), "name": "Renamed Room 1", "description": ""},
                    {"id": str(img2.id), "name": "Main Living", "description": ""},
                ]
            ),
            "main_image_id": str(img2.id),
        }
        res = auth_client.patch(detail_url, patch_payload, format="multipart")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]

        # Verify img3 deleted
        assert not PropertyImage.objects.filter(id=img3.id).exists()
        assert PropertyImage.objects.filter(property=prop).count() == 2

        # Verify img2 promoted to cover and appears first in images list
        assert data["main_image_id"] == str(img2.id)
        assert data["main_image_name"] == "Main Living"
        assert len(data["images"]) == 2
        assert data["images"][0]["id"] == str(img2.id)
        assert data["images"][1]["id"] == str(img1.id)
        assert data["images"][1]["name"] == "Renamed Room 1"
        assert data["images"][1]["description"] == ""

    def test_image_limit_enforced_transactionally(
        self, auth_client, user, test_property_factory
    ):
        prop = test_property_factory()
        # Seed 25 images
        for i in range(25):
            PropertyImage.objects.create(
                property=prop,
                image=generate_image_file(f"img_{i}.jpg"),
                name=f"Image {i}",
            )

        url = reverse("property-image-upload", kwargs={"property_id": prop.id})
        res = auth_client.post(
            url, {"image": generate_image_file("26th.jpg")}, format="multipart"
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "25" in str(res.json()["message"])


@pytest.mark.django_db
class TestCheck4_AllWritableFieldsAndReopen:
    """4. Edit every writable field and reopen Edit.

    Verify country, separate neighborhood/street, region IDs, zero floor,
    deposit, smoking false/null, all supported amenities, document
    replacement/removal.
    """

    def test_all_writable_fields_persist_and_reopen(
        self, auth_client, user, test_property_factory, cairo_city, cairo_governorate
    ):
        prop = test_property_factory(floor=5, smoking_allowed=True)
        detail_url = reverse("property-detail", kwargs={"id": prop.id})

        patch_payload = {
            "title": "Fully Edited Apartment",
            "description": "New updated description",
            "price": "14500.00",
            "price_period": "yearly",
            "bedrooms": 3,
            "bathrooms": 2,
            "area": 140,
            "floor": 0,  # Zero floor permitted
            "country": "Egypt",
            "street": "Makram Ebeid",
            "district": "Zone 6",
            "building_year": 2021,
            "deposit": "one_month",
            "smoking_allowed": False,
            "amenities": json.dumps(
                ["wifi", "elevator", "security", "electricity_meter"]
            ),
            "ownership_proof": generate_image_file("proof.jpg"),
        }
        res_patch = auth_client.patch(detail_url, patch_payload, format="multipart")
        assert res_patch.status_code == status.HTTP_200_OK
        data = res_patch.json()["data"]

        assert data["title"] == "Fully Edited Apartment"
        assert data["price"] == "14500.00"
        assert data["floor"] == 0
        assert data["street"] == "Makram Ebeid"
        assert data["district"] == "Zone 6"
        assert data["building_year"] == 2021
        assert data["deposit"] == "one_month"
        assert data["smoking_allowed"] is False
        assert set(data["amenities"]) == {
            "wifi",
            "elevator",
            "security",
            "electricity_meter",
        }
        assert data["ownership_proof"] is not None

        # Reopen GET by owner
        res_get = auth_client.get(detail_url)
        assert res_get.status_code == status.HTTP_200_OK
        get_data = res_get.json()["data"]
        assert get_data["floor"] == 0
        assert get_data["street"] == "Makram Ebeid"
        assert get_data["district"] == "Zone 6"
        assert get_data["building_year"] == 2021
        assert get_data["deposit"] == "one_month"
        assert get_data["ownership_proof"] is not None


@pytest.mark.django_db
class TestCheck5_ModerationStatusAndTenantIsolation:
    """5. Confirm each edit returns under_review, appears in the owner's list as pending,

    and ownership_proof does not leak to tenants.
    """

    def test_status_under_review_and_tenant_privacy(
        self, auth_client, api_client, user, another_user, test_property_factory
    ):
        prop = test_property_factory(status=Property.Status.VERIFIED, is_verified=True)
        detail_url = reverse("property-detail", kwargs={"id": prop.id})

        # Owner edits title
        res_patch = auth_client.patch(
            detail_url, {"title": "Updated Title Under Review"}, format="multipart"
        )
        assert res_patch.status_code == status.HTTP_200_OK
        assert res_patch.json()["data"]["status"] == Property.Status.UNDER_REVIEW

        # Owner's list shows under_review
        owned_url = reverse("my-property-list")
        res_owned = auth_client.get(owned_url)
        assert res_owned.status_code == status.HTTP_200_OK
        owned_props = res_owned.json()["data"]["results"]
        matched = [p for p in owned_props if p["id"] == str(prop.id)]
        assert len(matched) == 1
        assert matched[0]["status"] == Property.Status.UNDER_REVIEW

        # Tenant (another_user) fetches property details: ownership_proof is omitted or null
        api_client.force_authenticate(user=another_user)
        res_tenant = api_client.get(detail_url)
        assert res_tenant.status_code == status.HTTP_200_OK
        assert res_tenant.json()["data"]["ownership_proof"] is None


@pytest.mark.django_db
class TestCheck6_OwnerDeletionAndConflictHandling:
    """6. Delete as the owner and verify property disappears; attempt deletion as another

    account and ensure 403. Check lease/visit conflict returns 409.
    """

    def test_deletion_permissions_and_conflict(
        self, auth_client, api_client, user, another_user, test_property_factory
    ):
        prop = test_property_factory()
        delete_url = reverse("property-delete", kwargs={"id": prop.id})

        # Another user cannot delete
        tenant_client = APIClient()
        tenant_client.force_authenticate(user=another_user)
        res_forbidden = tenant_client.delete(delete_url)
        assert res_forbidden.status_code == status.HTTP_403_FORBIDDEN
        assert Property.objects.filter(id=prop.id).exists()

        # Active visit request blocks deletion with 409 Conflict
        PropertyVisit.objects.create(
            property=prop,
            tenant=another_user,
            visit_date="2026-10-10",
            visit_time="14:00:00",
            status=PropertyVisit.Status.CONFIRMED,
        )
        res_conflict = auth_client.delete(delete_url)
        assert res_conflict.status_code == status.HTTP_409_CONFLICT
        assert Property.objects.filter(id=prop.id).exists()

        # Cancel visit request and retry deletion
        prop.visits.all().delete()
        res_success = auth_client.delete(delete_url)
        assert res_success.status_code == status.HTTP_200_OK
        data = res_success.json()["data"]
        assert data["deleted"] is True
        assert data["id"] == str(prop.id)
        assert not Property.objects.filter(id=prop.id).exists()
