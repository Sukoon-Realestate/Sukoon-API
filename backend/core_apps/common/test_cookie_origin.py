"""A1-08: cookie-authenticated writes need same-origin proof; bearer clients are unaffected."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db
URL = "/api/v1/profiles/settings/"
BODY = {"language": "en"}


def _cookie_client(user):
    from core_apps.users.services.sessions import issue_refresh

    refresh = issue_refresh(user)
    client = APIClient()
    client.cookies["access"] = str(refresh.access_token)
    client.cookies["refresh"] = str(refresh)
    return client, refresh


def test_cookie_write_from_a_foreign_origin_is_refused(user):
    client, _ = _cookie_client(user)
    response = client.patch(URL, BODY, format="json", HTTP_ORIGIN="https://evil.example")
    assert response.status_code == 403


@pytest.mark.parametrize("origin", [None, "http://testserver"])
def test_cookie_write_without_origin_or_from_this_host_still_works(user, origin):
    client, _ = _cookie_client(user)
    extra = {"HTTP_ORIGIN": origin} if origin else {}
    response = client.patch(URL, BODY, format="json", **extra)
    assert response.status_code == 200, response.content


def test_configured_trusted_origin_is_accepted(user, settings):
    settings.COOKIE_TRUSTED_ORIGINS = ["https://app.sukoon.example"]
    client, _ = _cookie_client(user)
    assert client.patch(URL, BODY, format="json", HTTP_ORIGIN="https://app.sukoon.example").status_code == 200


def test_cookie_reads_are_not_affected(user):
    client, _ = _cookie_client(user)
    assert client.get(URL, HTTP_ORIGIN="https://evil.example").status_code == 200


def test_bearer_clients_are_unaffected_by_origin(user):
    from core_apps.users.services.sessions import issue_refresh

    token = issue_refresh(user).access_token
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert client.patch(URL, BODY, format="json", HTTP_ORIGIN="https://evil.example").status_code == 200


def test_cookie_refresh_from_a_foreign_origin_is_refused_but_body_refresh_works(user):
    client, refresh = _cookie_client(user)
    url = reverse("refresh")
    assert client.post(url, {}, format="json", HTTP_ORIGIN="https://evil.example").status_code == 403
    body_client = APIClient()
    response = body_client.post(url, {"refresh": str(refresh)}, format="json", HTTP_ORIGIN="https://evil.example")
    assert response.status_code == 200, response.content


def test_enforcement_switch(user, settings):
    settings.COOKIE_ORIGIN_ENFORCEMENT = False
    client, _ = _cookie_client(user)
    assert client.patch(URL, BODY, format="json", HTTP_ORIGIN="https://evil.example").status_code == 200
