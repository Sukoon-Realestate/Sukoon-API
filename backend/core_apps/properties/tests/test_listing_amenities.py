import pytest
from django.urls import reverse

from core_apps.properties.models import Property
from core_apps.properties.tests.test_views import _create_property


@pytest.mark.django_db
@pytest.mark.parametrize("route", ["property-list", "property-homepage-list"])
def test_listing_returns_only_available_amenities(api_client, user, route):
    prop = _create_property(
        owner=user,
        status=Property.Status.VERIFIED,
        has_wifi=True,
        has_air_conditioning=True,
        has_garage=False,
    )
    response = api_client.get(reverse(route))
    assert response.status_code == 200
    data = response.json()["data"]
    rows = data["results"] if isinstance(data, dict) else data
    row = next(item for item in rows if item["id"] == str(prop.id))
    assert "wifi" in row["amenities"]
    assert "air_conditioning" in row["amenities"]
    assert "garage" not in row["amenities"]
