"""Old clients must never be told an unscheduled visit is happening today."""
import pytest
from django.urls import reverse
from django.utils import timezone
from core_apps.properties.models import PropertyVisit
from .test_views import _create_property

pytestmark = pytest.mark.django_db

@pytest.mark.parametrize("workspace", ["individual", "owner", "student", "company"])
def test_retired_reminder_never_returns_a_calendar_banner(auth_client, user, another_user, workspace):
    prop = _create_property(owner=another_user)
    PropertyVisit.objects.create(property=prop, tenant=user, status="confirmed")
    PropertyVisit.objects.create(property=prop, tenant=user, status="confirmed", visit_date=timezone.localdate(), visit_time="14:00")
    response = auth_client.get(reverse("home-visit-reminder"), {"workspace": workspace})
    assert response.status_code == 200
    assert response.json()["data"]["banner"] is None
    assert response["Cache-Control"] == "private, no-store"
    response = auth_client.get(reverse("property-homepage-list"))
    assert response.json()["data"]["banner"] is None

def test_compatibility_endpoint_requires_authentication(api_client):
    assert api_client.get(reverse("home-visit-reminder")).status_code == 401
