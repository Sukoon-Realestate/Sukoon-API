import pytest
from django.urls import reverse
from rest_framework import status

PROFILE_LIST_URL = reverse("profile-list")
PROFILE_DETAIL_URL = reverse("profile-detail")
PROFILE_UPDATE_URL = reverse("profile-update")


@pytest.mark.django_db
class TestProfileListView:
    def test_unauthenticated_request_returns_401(self, api_client):
        res = api_client.get(PROFILE_LIST_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_paginated_profiles(self, auth_client):
        res = auth_client.get(PROFILE_LIST_URL)
        assert res.status_code == status.HTTP_200_OK
        assert "results" in res.data

    def test_excludes_staff_profiles(self, auth_client, superuser):
        res = auth_client.get(PROFILE_LIST_URL)
        profile_ids = [str(p["id"]) for p in res.data["results"]]
        assert str(superuser.profile.id) not in profile_ids

    def test_filter_by_gender(self, auth_client):
        res = auth_client.get(PROFILE_LIST_URL, {"gender": "male"})
        assert res.status_code == status.HTTP_200_OK
        for profile in res.data["results"]:
            assert profile["gender"] == "male"

    def test_search_by_first_name(self, auth_client, user):
        res = auth_client.get(PROFILE_LIST_URL, {"search": user.first_name})
        assert res.status_code == status.HTTP_200_OK
        ids = [str(p["id"]) for p in res.data["results"]]
        assert str(user.profile.id) in ids


@pytest.mark.django_db
class TestProfileDetailView:
    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(PROFILE_DETAIL_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_own_profile(self, auth_client, user):
        res = auth_client.get(PROFILE_DETAIL_URL)
        assert res.status_code == status.HTTP_200_OK
        assert str(user.profile.id) == res.data["id"]

    def test_does_not_return_other_user_profile(self, auth_client, another_user):
        res = auth_client.get(PROFILE_DETAIL_URL)
        assert res.status_code == status.HTTP_200_OK
        assert str(another_user.profile.id) != res.data["id"]


@pytest.mark.django_db
class TestProfileUpdateView:
    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.patch(PROFILE_UPDATE_URL, {}, format="json")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_name_updates_user_fields(self, auth_client, user):
        res = auth_client.patch(
            PROFILE_UPDATE_URL,
            {"first_name": "Updated", "last_name": "Name"},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == "Updated"
        assert user.last_name == "Name"

    def test_update_gender(self, auth_client, user):
        res = auth_client.patch(
            PROFILE_UPDATE_URL,
            {"gender": "female"},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        user.profile.refresh_from_db()
        assert user.profile.gender == "female"

    def test_update_kyc_fields(self, auth_client, user):
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9'
            b'\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00'
            b'\x00\x02\x02\x4c\x01\x00\x3b'
        )
        avatar_file = SimpleUploadedFile("avatar.gif", small_gif, content_type="image/gif")
        face_file = SimpleUploadedFile("face.gif", small_gif, content_type="image/gif")
        back_file = SimpleUploadedFile("back.gif", small_gif, content_type="image/gif")
        selfie_file = SimpleUploadedFile("selfie.gif", small_gif, content_type="image/gif")

        mock_upload_response = lambda file, **kwargs: {
            "public_id": f"mocked_{file.name}" if hasattr(file, "name") else "mocked_file",
            "url": f"https://res.cloudinary.com/mocked/{file.name}" if hasattr(file, "name") else "https://res.cloudinary.com/mocked/file",
            "secure_url": f"https://res.cloudinary.com/mocked/{file.name}" if hasattr(file, "name") else "https://res.cloudinary.com/mocked/file",
            "format": "gif",
            "resource_type": "image",
            "version": 123456,
            "type": "upload",
        }

        with patch("cloudinary.uploader.upload", side_effect=mock_upload_response):
            res = auth_client.patch(
                PROFILE_UPDATE_URL,
                {
                    "national_id": "123456789",
                    "avatar": avatar_file,
                    "id_face": face_file,
                    "id_back": back_file,
                    "confirmation_selfi": selfie_file,
                },
                format="multipart",
            )
        assert res.status_code == status.HTTP_200_OK
        user.profile.refresh_from_db()
        assert user.profile.national_id == "123456789"
        assert "avatar" in str(user.profile.avatar)
        assert "face" in str(user.profile.id_face)
        assert "back" in str(user.profile.id_back)
        assert "selfie" in str(user.profile.confirmation_selfi)

