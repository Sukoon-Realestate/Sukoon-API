import uuid

import pytest
from rest_framework.test import APIClient

from core_apps.features.models import SearchAlert
from core_apps.users.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="features@example.com",
        password="strong-pass",
        first_name="Feature",
        last_name="User",
    )


@pytest.fixture
def client(user):
    api = APIClient()
    api.force_authenticate(user)
    return api


@pytest.mark.django_db
def test_configuration_is_free_and_workspace_scoped(client):
    response = client.get("/api/v1/features/v1/configuration/?workspace=owner&lang=en")
    assert response.status_code == 200
    assert response.json()["key"] == "success"
    assert response.json()["data"]["workspace"] == "owner"
    assert response.data["workspace"] == "owner"
    assert response.data["boost_options"][0]["duration_days"] > 0
    assert "products" not in response.data


@pytest.mark.django_db
def test_alert_create_replays_same_request_key(client):
    request_key = str(uuid.uuid4())
    payload = {
        "name": "Near work",
        "cadence": "daily",
        "filters": {"district": "Maadi", "page": 1},
        "request_key": request_key,
    }
    first = client.post("/api/v1/features/v1/search-alerts/", payload, format="json")
    second = client.post("/api/v1/features/v1/search-alerts/", payload, format="json")
    assert first.status_code == second.status_code == 201
    assert first.data["id"] == second.data["id"]
    assert SearchAlert.objects.count() == 1


@pytest.mark.django_db
def test_alert_request_key_conflict_is_409(client):
    request_key = str(uuid.uuid4())
    base = {
        "name": "One",
        "cadence": "daily",
        "filters": {},
        "request_key": request_key,
    }
    assert (
        client.post(
            "/api/v1/features/v1/search-alerts/", base, format="json"
        ).status_code
        == 201
    )
    changed = {**base, "name": "Different"}
    assert (
        client.post(
            "/api/v1/features/v1/search-alerts/", changed, format="json"
        ).status_code
        == 409
    )


@pytest.mark.django_db
def test_alert_revision_protects_updates(client, user):
    alert = SearchAlert.objects.create(
        user=user, name="Alert", cadence="instant", filters={}
    )
    stale = client.patch(
        f"/api/v1/features/v1/search-alerts/{alert.id}/",
        {"enabled": False, "revision": 9, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert stale.status_code == 409
    ok = client.patch(
        f"/api/v1/features/v1/search-alerts/{alert.id}/",
        {"enabled": False, "revision": 1, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert ok.status_code == 200
    alert.refresh_from_db()
    assert alert.enabled is False
    assert alert.revision == 2


@pytest.mark.django_db
def test_feature_routes_require_authentication():
    response = APIClient().get("/api/v1/features/v1/configuration/?workspace=tenant")
    assert response.status_code in {401, 403}
