from datetime import date, time
import pytest
from django.urls import reverse
from rest_framework import status

from core_apps.profiles.models import Profile
from core_apps.properties.models import (
    City,
    Governorate,
    Property,
    PropertyType,
    PropertyVisit,
    PropertyVisitReview,
    SavedProperty,
)

MY_ACCOUNT_URL = reverse("my-account")
ACCOUNT_SUMMARY_URL = reverse("account-summary")
PROFILE_EDIT_URL = reverse("profile-edit")


def create_test_property(owner):
    governorate, _ = Governorate.objects.get_or_create(
        slug="cairo", defaults={"name": "Cairo"}
    )
    city, _ = City.objects.get_or_create(
        governorate=governorate,
        slug="nasr-city",
        defaults={"name": "Nasr City"},
    )
    property_type, _ = PropertyType.objects.get_or_create(
        slug="apartment", defaults={"name": "Apartment"}
    )
    return Property.objects.create(
        owner=owner,
        title="شقة فاخرة",
        price=6500,
        bedrooms=2,
        bathrooms=1,
        area=90,
        district="مدينة نصر",
        governorate=governorate,
        city=city,
        property_type=property_type,
    )


@pytest.mark.django_db
class TestMyAccountScreenAPI:
    """Tests for Screen 1: 'حسابي' (My Account)."""

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(MY_ACCOUNT_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_returns_full_screen_structure(self, auth_client, user):
        user.first_name = "أحمد"
        user.last_name = "محمد علي"
        user.is_verified = True
        user.save()

        res = auth_client.get(MY_ACCOUNT_URL)
        assert res.status_code == status.HTTP_200_OK

        data = res.json()["data"]
        # User card assertions
        assert data["user"]["full_name"] == "أحمد محمد علي"
        assert data["user"]["is_verified"] is True
        assert data["user"]["verification_badge"] == "موثّق"
        assert data["user"]["role_label"] == "مستأجر"
        assert "عضو منذ" in data["user"]["member_since_label"]

        # Stats assertions
        assert "saved_count" in data["stats"]
        assert "visits_count" in data["stats"]
        assert "reviews_count" in data["stats"]

        # Menu items
        assert "visit_requests" in data["menu_items"]
        assert data["menu_items"]["visit_requests"]["title"] == "طلبات الزيارة"
        assert "contracts" in data["menu_items"]
        assert data["menu_items"]["contracts"]["title"] == "عقودي"
        assert "reviews" in data["menu_items"]
        assert data["menu_items"]["reviews"]["title"] == "تقييماتي"
        assert "verification" in data["menu_items"]
        assert data["menu_items"]["verification"]["title"] == "التوثيق والخصوصية"

        # Account details
        assert data["account_details"]["name"] == "أحمد محمد علي"
        assert data["account_details"]["email"] == user.email

    def test_screen_stats_reflect_user_activity(self, auth_client, user, another_user):
        property_obj = create_test_property(another_user)

        # 1. Add saved property
        SavedProperty.objects.create(user=user, property=property_obj)

        # 2. Add visit
        visit = PropertyVisit.objects.create(
            tenant=user,
            property=property_obj,
            visit_date=date(2026, 7, 20),
            visit_time=time(14, 0),
            status=PropertyVisit.Status.CONFIRMED,
        )

        # 3. Add review
        PropertyVisitReview.objects.create(
            visit=visit,
            overall_rating=5,
            cleanliness_rating=5,
            listing_accuracy_rating=5,
            owner_interaction_rating=5,
            comment="تجربة ممتازة",
        )

        res = auth_client.get(MY_ACCOUNT_URL)
        assert res.status_code == status.HTTP_200_OK

        data = res.json()["data"]
        assert data["stats"]["saved_count"] == 1
        assert data["stats"]["visits_count"] == 1
        assert data["stats"]["reviews_count"] == 1
        assert data["menu_items"]["contracts"]["count"] == 1


@pytest.mark.django_db
class TestAccountSummaryScreenAPI:
    """Tests for Screen 2: 'ملخص الحساب' (Account Summary)."""

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(ACCOUNT_SUMMARY_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_returns_structure_and_completion(self, auth_client, user):
        user.first_name = "محمد"
        user.last_name = "أحمد"
        user.is_verified = True
        user.save()
        user.profile.phone_number = "+201012345432"
        user.profile.birth_date = date(1995, 3, 15)
        user.profile.gender = Profile.Gender.MALE
        user.profile.save()

        res = auth_client.get(ACCOUNT_SUMMARY_URL)
        assert res.status_code == status.HTTP_200_OK

        data = res.json()["data"]
        assert data["user"]["full_name"] == "محمد أحمد"
        assert data["user"]["initial"] == "م"
        assert data["user"]["role_label"] == "مستأجر"
        assert data["user"]["profile_completion_percentage"] == 80
        assert data["user"]["profile_completion_label"] == "اكتمال الملف"

        assert data["identity_verification"]["is_verified"] is True
        assert data["identity_verification"]["title"] == "هويتك موثّقة"
        assert data["identity_verification"]["status_label"] == "مكتمل"

        assert "saved_properties_count" in data["stats"]
        assert "completed_visits_count" in data["stats"]
        assert "active_chats_count" in data["stats"]

        assert "saved_properties" in data["shortcuts"]
        assert "visits_history" in data["shortcuts"]
        assert "identity_verification" in data["shortcuts"]


@pytest.mark.django_db
class TestProfileEditScreenAPI:
    """Tests for Screen 3: 'تعديل الملف' (Edit Profile)."""

    def test_unauthenticated_returns_401(self, api_client):
        assert (
            api_client.get(PROFILE_EDIT_URL).status_code == status.HTTP_401_UNAUTHORIZED
        )
        assert (
            api_client.patch(PROFILE_EDIT_URL, {}).status_code
            == status.HTTP_401_UNAUTHORIZED
        )

    def test_get_edit_profile_prefilled_data(self, auth_client, user):
        user.first_name = "محمد"
        user.last_name = "أحمد"
        user.save()
        user.profile.phone_number = "+201012345432"
        user.profile.birth_date = date(1995, 3, 15)
        user.profile.gender = Profile.Gender.MALE
        user.profile.save()

        res = auth_client.get(PROFILE_EDIT_URL)
        assert res.status_code == status.HTTP_200_OK

        data = res.json()["data"]
        assert data["full_name"] == "محمد أحمد"
        assert data["email"] == user.email
        assert data["masked_phone_number"] == "010****432"
        assert data["birth_date"] == "1995-03-15"
        assert data["birth_date_label"] == "15 مارس 1995"
        assert data["gender"] == "male"
        assert data["gender_label"] == "ذكر"

    def test_patch_updates_profile_and_full_name(self, auth_client, user):
        payload = {
            "full_name": "علي محمود",
            "phone_number": "+201098765432",
            "birth_date": "1992-06-20",
            "gender": "male",
        }

        res = auth_client.patch(PROFILE_EDIT_URL, payload, format="json")
        assert res.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.first_name == "علي"
        assert user.last_name == "محمود"
        assert str(user.profile.phone_number) == "+201098765432"
        assert user.profile.birth_date == date(1992, 6, 20)

        data = res.json()["data"]
        assert data["full_name"] == "علي محمود"
        assert data["masked_phone_number"] == "010****432"
        assert data["birth_date_label"] == "20 يونيو 1992"

    def test_patch_invalid_phone_number_returns_400(self, auth_client):
        res = auth_client.patch(
            PROFILE_EDIT_URL, {"phone_number": "invalid-phone"}, format="json"
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_invalid_gender_returns_400(self, auth_client):
        res = auth_client.patch(
            PROFILE_EDIT_URL, {"gender": "unknown_gender"}, format="json"
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_updates_avatar_with_multipart_file(self, auth_client, user):
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile

        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9"
            b"\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00"
            b"\x00\x02\x02\x4c\x01\x00\x3b"
        )
        avatar_file = SimpleUploadedFile(
            "new_avatar.gif", small_gif, content_type="image/gif"
        )
        mock_upload_response = lambda file, **kwargs: {
            "public_id": "mocked_avatar",
            "url": "https://res.cloudinary.com/mocked/new_avatar.gif",
            "secure_url": "https://res.cloudinary.com/mocked/new_avatar.gif",
            "format": "gif",
            "resource_type": "image",
            "version": 123456,
            "type": "upload",
        }

        with patch("cloudinary.uploader.upload", side_effect=mock_upload_response):
            res = auth_client.patch(
                PROFILE_EDIT_URL,
                {"avatar": avatar_file},
                format="multipart",
            )
        assert res.status_code == status.HTTP_200_OK
        user.profile.refresh_from_db()
        assert user.profile.avatar is not None

        data = res.json()["data"]
        assert data["avatar"] is not None
        assert data["profile_image"] == data["avatar"]

    def test_patch_updates_avatar_with_profile_image_alias(self, auth_client, user):
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile

        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9"
            b"\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00"
            b"\x00\x02\x02\x4c\x01\x00\x3b"
        )
        profile_img_file = SimpleUploadedFile(
            "profile_pic.gif", small_gif, content_type="image/gif"
        )
        mock_upload_response = lambda file, **kwargs: {
            "public_id": "mocked_pic",
            "url": "https://res.cloudinary.com/mocked/profile_pic.gif",
            "secure_url": "https://res.cloudinary.com/mocked/profile_pic.gif",
            "format": "gif",
            "resource_type": "image",
            "version": 123456,
            "type": "upload",
        }

        with patch("cloudinary.uploader.upload", side_effect=mock_upload_response):
            res = auth_client.patch(
                PROFILE_EDIT_URL,
                {"profile_image": profile_img_file},
                format="multipart",
            )
        assert res.status_code == status.HTTP_200_OK
        user.profile.refresh_from_db()
        assert user.profile.avatar is not None
        data = res.json()["data"]
        assert data["avatar"] is not None
        assert data["profile_image"] == data["avatar"]

    def test_patch_updates_avatar_with_base64_data_uri(self, auth_client, user):
        from unittest.mock import patch

        base64_gif = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
        mock_upload_response = lambda file, **kwargs: {
            "public_id": "mocked_base64",
            "url": "https://res.cloudinary.com/mocked/base64.gif",
            "secure_url": "https://res.cloudinary.com/mocked/base64.gif",
            "format": "gif",
            "resource_type": "image",
            "version": 123456,
            "type": "upload",
        }

        with patch("cloudinary.uploader.upload", side_effect=mock_upload_response):
            res = auth_client.patch(
                PROFILE_EDIT_URL,
                {"avatar": base64_gif},
                format="json",
            )
        assert res.status_code == status.HTTP_200_OK
        user.profile.refresh_from_db()
        assert user.profile.avatar is not None

    def test_patch_invalid_image_file_returns_400(self, auth_client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        text_file = SimpleUploadedFile(
            "not_an_image.txt", b"plain text content", content_type="text/plain"
        )
        res = auth_client.patch(
            PROFILE_EDIT_URL,
            {"avatar": text_file},
            format="multipart",
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_updates_profile_avatar(self, auth_client, user):
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile

        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9"
            b"\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00"
            b"\x00\x02\x02\x4c\x01\x00\x3b"
        )
        avatar_file = SimpleUploadedFile(
            "put_avatar.gif", small_gif, content_type="image/gif"
        )
        mock_upload_response = lambda file, **kwargs: {
            "public_id": "mocked_put_avatar",
            "url": "https://res.cloudinary.com/mocked/put_avatar.gif",
            "secure_url": "https://res.cloudinary.com/mocked/put_avatar.gif",
            "format": "gif",
            "resource_type": "image",
            "version": 123456,
            "type": "upload",
        }

        with patch("cloudinary.uploader.upload", side_effect=mock_upload_response):
            res = auth_client.put(
                PROFILE_EDIT_URL,
                {"avatar": avatar_file, "full_name": "سامي خالد"},
                format="multipart",
            )
        assert res.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == "سامي"
        assert user.last_name == "خالد"
        assert user.profile.avatar is not None
