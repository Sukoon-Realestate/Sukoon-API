"""List filters are enforced before pagination and within the authorized scope."""
import copy
import uuid

import pytest
from rest_framework.test import APIClient

from core_apps.features.services.rental_phase3 import generate_billing_schedule
from core_apps.users.models import User
from .test_rental_phase3 import phase3_lease  # noqa: F401


@pytest.mark.django_db
@pytest.mark.parametrize("workspace", ["owner", "tenant"])
def test_lease_detail_selects_exact_resource_and_denies_other_accounts(phase3_lease, workspace):
    owner, tenant, lease = phase3_lease
    client = APIClient()
    client.force_authenticate(owner if workspace == "owner" else tenant)
    endpoint = f"/api/v1/features/v1/leases/{lease.id}/"
    response = client.get(endpoint)
    assert response.status_code == 200
    assert str(response.json()["data"]["id"]) == str(lease.id)
    assert client.get(f"/api/v1/features/v1/leases/{uuid.uuid4()}/").status_code == 404
    client.force_authenticate(User.objects.create_user(email="detail-outsider@example.test"))
    hidden = client.get(endpoint)
    assert hidden.status_code in (403, 404)
    assert "id" not in (hidden.json().get("data") or {})


@pytest.mark.django_db
@pytest.mark.parametrize("workspace", ["owner", "tenant"])
@pytest.mark.parametrize("resource", ["leases", "rent-invoices"])
def test_resource_filter_is_applied_before_pagination(phase3_lease, workspace, resource):
    owner, tenant, first = phase3_lease
    other_property = copy.copy(first.property)
    other_property.pk = None
    other_property.id = uuid.uuid4()
    other_property.title = "Other property"
    other_property.save(force_insert=True)
    second = copy.copy(first)
    second.pk = None
    second.id = uuid.uuid4()
    second.property = other_property
    second.offer_id = str(uuid.uuid4())
    second.save(force_insert=True)
    for lease in (first, second):
        list(generate_billing_schedule(lease))
    client = APIClient()
    client.force_authenticate(owner if workspace == "owner" else tenant)
    key = "property_id" if resource == "leases" else "lease_id"
    selected = str(first.property.id if resource == "leases" else first.id)
    response = client.get(f"/api/v1/features/v1/{resource}/", {
        "workspace": workspace, key: selected, "page_size": 1,
    })
    assert response.status_code == 200
    # Validate the rendered wire contract, including subsequent pages.
    payload = response.json()
    assert payload["data"]
    total = int(response["X-Total-Pages"])
    for page in range(1, total + 1):
        response = client.get(f"/api/v1/features/v1/{resource}/", {
            "workspace": workspace, key: selected, "page_size": 1, "page": page,
        })
        assert response.status_code == 200
        assert all(str(item[key]) == selected for item in response.json()["data"])
    client.force_authenticate(User.objects.create_user(email="filter-outsider@example.test"))
    response = client.get(f"/api/v1/features/v1/{resource}/", {"workspace": workspace, key: selected})
    assert response.status_code == 200
    assert response.json()["data"] == []
