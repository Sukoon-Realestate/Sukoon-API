"""Mobile Accepted uses confirmed for both tenant collections in either locale."""
import pytest
from django.urls import reverse

from core_apps.common.contract_testing import api_json
from core_apps.properties.models import PropertyVisit
from .test_visit_phone_disclosure import make_property, make_visit


@pytest.mark.django_db
@pytest.mark.requires_postgres
@pytest.mark.parametrize("route", ["tenant-visit-list", "tenant-visit-request-list"])
@pytest.mark.parametrize("language", ["ar", "en"])
@pytest.mark.parametrize("has_accepted", [False, True])
def test_accepted_wire_filter_returns_only_confirmed_or_successful_empty(
    api_client, user, another_user, apartment_type, cairo_city,
    cairo_governorate, route, language, has_accepted,
):
    property_obj = make_property(
        another_user, apartment_type, cairo_city, cairo_governorate,
    )
    make_visit(property_obj, user)
    accepted = make_visit(property_obj, user, PropertyVisit.Status.CONFIRMED) if has_accepted else None
    api_client.force_authenticate(user)
    response = api_client.get(
        reverse(route), {"status": "confirmed"}, HTTP_ACCEPT_LANGUAGE=language,
    )
    assert response.status_code == 200
    rows = api_json(response)["data"]["results"]
    assert [row["id"] for row in rows] == ([str(accepted.id)] if accepted else [])
