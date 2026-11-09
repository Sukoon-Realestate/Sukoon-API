"""Sprint 02 (A1-07): refresh accepts JSON/form/multipart/cookie input without
mutating request data; malformed bodies are 400, rotation/revocation intact."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from core_apps.users.services.sessions import issue_refresh, revoke_all

pytestmark = pytest.mark.django_db
URL = reverse("refresh")


@pytest.fixture
def refresh(user):
    return str(issue_refresh(user))


@pytest.mark.parametrize("fmt", ["json", "multipart"])
def test_body_refresh_works_for_json_and_multipart(refresh, fmt):
    response = APIClient().post(URL, {"refresh": refresh}, format=fmt)
    assert response.status_code == 200, response.content
    assert response.cookies["access"].value and response.cookies["refresh"].value


def test_form_urlencoded_refresh_works(refresh):
    response = APIClient().post(
        URL, f"refresh={refresh}", content_type="application/x-www-form-urlencoded"
    )
    assert response.status_code == 200, response.content


def test_cookie_refresh_with_form_body_does_not_touch_immutable_data(refresh):
    client = APIClient()
    client.cookies["refresh"] = refresh
    response = client.post(URL, {"unrelated": "x"}, format="multipart")
    assert response.status_code == 200, response.content


@pytest.mark.parametrize(
    "body", [[], ["token"], "token", 5, {"refresh": 5}, {"refresh": ["a"]},
             {"refresh": {"a": 1}}, {"refresh": True}, {"refresh": "x" * 5000}],
    ids=repr,
)
def test_malformed_refresh_bodies_are_400(body):
    response = APIClient().post(URL, body, format="json")
    assert response.status_code == 400, response.content


def test_invalid_and_revoked_refresh_tokens_stay_401(user, refresh):
    assert APIClient().post(URL, {"refresh": "not-a-jwt"}, format="json").status_code == 401
    revoke_all(user)
    assert APIClient().post(URL, {"refresh": refresh}, format="json").status_code == 401
