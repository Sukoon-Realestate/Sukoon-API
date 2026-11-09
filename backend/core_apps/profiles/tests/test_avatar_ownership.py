"""A1-01 failing-before case: a borrowed provider reference must not become the user's avatar.

CloudinarySerializerField returns any non-data-URI string unchanged, so a user can set another
account's public ID as their avatar; account closure later queues that ID for provider
deletion. Strict xfail: the Sprint 01 fix must make this pass and remove the marker.
"""

import pytest
from django.urls import reverse

BORROWED = "image/upload/v1700000000/someone-elses-avatar"


@pytest.mark.django_db
@pytest.mark.xfail(strict=True, reason="A1-01: arbitrary provider references are accepted as owned avatars (Sprint 01)")
def test_borrowed_public_id_is_not_attached_as_owned_avatar(auth_client, user):
    response = auth_client.patch(reverse("profile-edit"), {"avatar": BORROWED}, format="json")

    user.profile.refresh_from_db()
    stored = str(getattr(user.profile.avatar, "public_id", user.profile.avatar) or "")
    assert "someone-elses-avatar" not in stored, f"borrowed reference stored (HTTP {response.status_code})"
