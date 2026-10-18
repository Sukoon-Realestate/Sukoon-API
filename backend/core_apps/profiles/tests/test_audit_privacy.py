import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "query", [{}, {"search": "Test"}, {"gender": "male", "page": 2}]
)
def test_legacy_directory_never_discloses_another_identity(
    auth_client, another_user, query
):
    another_user.profile.national_id = "29001011234567"
    another_user.profile.save()
    response = auth_client.get(reverse("profile-list"), query)
    assert response.status_code == 410
    assert another_user.email not in response.content.decode()
    assert another_user.profile.national_id not in response.content.decode()


@pytest.mark.parametrize(
    "payload",
    [
        {"phone_number": "+14155552671"},
        {"national_id": "29001011234567"},
        {"id_face": "https://example.com/replacement.png"},
    ],
)
def test_legacy_editor_cannot_change_verified_contacts_or_identity(
    auth_client, user, payload
):
    before = (
        str(user.profile.phone_number),
        user.profile.national_id,
        str(user.profile.id_face),
    )
    response = auth_client.patch(reverse("profile-update"), payload, format="json")
    assert response.status_code == 403
    user.profile.refresh_from_db()
    assert (
        str(user.profile.phone_number),
        user.profile.national_id,
        str(user.profile.id_face),
    ) == before
