"""A1-01: borrowed provider references must never become owned avatars or deletion targets.

Sprint 00 recorded this as a strict xfail. Sprint 01 refuses borrowed references at input,
records provenance for real uploads, and erases on closure only what the account uploaded.
"""

from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from core_apps.profiles.models import Profile, ProfileMediaUpload

BORROWED = "image/upload/v1700000000/someone-elses-avatar"
GIF = (
    b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00"
    b"\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b"
)


def _upload(file, **kwargs):
    return {
        "public_id": "profile_documents/avatar/mine",
        "url": "https://res.cloudinary.com/test_cloud/image/upload/v1/profile_documents/avatar/mine.gif",
        "secure_url": "https://res.cloudinary.com/test_cloud/image/upload/v1/profile_documents/avatar/mine.gif",
        "format": "gif",
        "resource_type": "image",
        "version": 1,
        "type": "upload",
    }


@pytest.mark.django_db
@pytest.mark.parametrize("route", ["profile-edit", "profile-update"])
@pytest.mark.parametrize("field", ["avatar", "profile_image", "image"])
@pytest.mark.parametrize(
    "reference",
    [BORROWED, "https://res.cloudinary.com/test_cloud/image/upload/v1/someone-elses-avatar.jpg"],
)
def test_borrowed_reference_is_refused_on_every_avatar_input(auth_client, user, route, field, reference):
    if route == "profile-update" and field != "avatar":
        pytest.skip("aliases exist only on the edit screen")
    response = auth_client.patch(reverse(route), {field: reference}, format="json")

    assert response.status_code == 400
    user.profile.refresh_from_db()
    stored = str(getattr(user.profile.avatar, "public_id", user.profile.avatar) or "")
    assert "someone-elses-avatar" not in stored


@pytest.mark.django_db
def test_upload_records_provenance_and_echoing_the_current_value_is_a_no_op(auth_client, user):
    with patch("cloudinary.uploader.upload", side_effect=_upload):
        response = auth_client.patch(
            reverse("profile-edit"),
            {"avatar": SimpleUploadedFile("a.gif", GIF, content_type="image/gif")},
            format="multipart",
        )
    assert response.status_code == 200
    receipt = ProfileMediaUpload.objects.get(user=user)
    assert (receipt.field, receipt.public_id, receipt.storage_type) == (
        "avatar", "profile_documents/avatar/mine", "upload"
    )

    current = response.json()["data"]["avatar"] if "data" in response.json() else response.json()["avatar"]
    with patch("cloudinary.uploader.upload") as upload:
        echoed = auth_client.patch(reverse("profile-edit"), {"avatar": current, "full_name": "Same Avatar"}, format="json")
    assert echoed.status_code == 200, echoed.content
    upload.assert_not_called()
    assert Profile.objects.get(user=user).avatar.public_id == "profile_documents/avatar/mine"


@pytest.mark.django_db
def test_clearing_the_avatar_is_still_allowed(auth_client, user):
    Profile.objects.filter(user=user).update(avatar="image/upload/v1/profile_documents/avatar/mine.gif")
    response = auth_client.patch(reverse("profile-edit"), {"avatar": None}, format="json")
    assert response.status_code == 200
    assert not Profile.objects.get(user=user).avatar


@pytest.mark.django_db
def test_provenance_audit_is_read_only_and_reports_unproven_and_shared(user, another_user):
    import json
    from io import StringIO

    from django.core.management import call_command

    shared = "image/upload/v1/profile_documents/avatar/shared.jpg"
    Profile.objects.filter(user__in=[user, another_user]).update(avatar=shared)
    before = [str(v) for v in Profile.objects.order_by("pk").values_list("avatar", flat=True)]
    out = StringIO()
    call_command("audit_profile_media_provenance", "--json", stdout=out)
    report = json.loads(out.getvalue())
    assert report["unproven_references"] == 2
    assert report["shared_references"] == ["profile_documents/avatar/shared"]
    assert [str(v) for v in Profile.objects.order_by("pk").values_list("avatar", flat=True)] == before
    assert not ProfileMediaUpload.objects.exists()
