from datetime import date, time

import pytest
from rest_framework.test import APIClient
from core_apps.features.tests.test_rental_phase3 import phase3_lease  # noqa: F401
from core_apps.properties.models import PropertyVisit


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["owner/visits/requests/", "visits/received/"])
@pytest.mark.parametrize("status", ["pending", "confirmed", "canceled", "rejected", "completed"])
def test_owner_status_filter_precedes_pagination_and_preserves_global_counts(phase3_lease, path, status):
    owner, tenant, lease = phase3_lease
    for index, value in enumerate(PropertyVisit.Status.values):
        for day in (1, 2):
            PropertyVisit.objects.create(property=lease.property, tenant=tenant,
                status=value, visit_date=date(2027, 1, day), visit_time=time(12 + index))
    client = APIClient()
    client.force_authenticate(owner)
    response = client.get(f"/api/v1/properties/{path}", {"status": status, "page_size": 1})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["tabs"]["all"] == 8
    assert data["tabs"]["canceled"] == 2
    assert data["tabs"]["completed"] == 0
    assert data["count"] == (0 if status == "completed" else 2)
    if status == "completed":
        assert data["results"] == []
    else:
        for page in (1, 2):
            response = client.get(f"/api/v1/properties/{path}", {"status": status, "page_size": 1, "page": page})
            assert response.status_code == 200
            assert len(response.json()["data"]["results"]) == 1
            assert response.json()["data"]["results"][0]["status"] == status
    client.force_authenticate(tenant)
    response = client.get(f"/api/v1/properties/{path}", {"status": status})
    assert response.status_code == 200
    assert response.json()["data"]["results"] == []
    assert response.json()["data"]["tabs"]["all"] == 0
