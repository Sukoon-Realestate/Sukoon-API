from copy import deepcopy
import uuid
import pytest
from core_apps.features.models import RentalChange
from .test_rental_phase5 import client_for, phase5_lease

pytestmark = pytest.mark.django_db


def test_comparison_binds_authorized_snapshots_and_old_approval_is_rejected(phase5_lease):
    owner, tenant, lease = phase5_lease
    change = RentalChange.objects.create(lease=lease, requester=owner,
        kind="amendment", status="proposed", previous_terms=deepcopy(lease.terms),
        terms={**lease.terms, "included_services": ["Internet"]})
    url = f"/api/v1/features/v1/amendments/{change.id}/"
    initial = client_for(tenant).get(url)
    assert initial.status_code == 200, initial.data
    comparison = initial.data["comparison"]
    assert comparison["base_id"] == str(lease.id)
    assert comparison["base_available"] is True
    assert comparison["base_revision"] is None
    assert comparison["current_id"] == str(change.id)
    assert set(comparison["required_approvals"]) == {str(owner.id), str(tenant.id)}
    revision = change.revision
    change.terms = {**change.terms, "included_services": ["Internet", "Cleaning"]}
    change.revision += 1
    change.content_revision += 1
    change.save()
    updated = client_for(tenant).get(url).data["comparison"]
    assert comparison["digest"] != updated["digest"]
    assert comparison["base_digest"] == updated["base_digest"]
    stale = client_for(tenant).post(url+"respond/", {
        "expected_revision": revision, "request_key": str(uuid.uuid4()), "decision": "accept",
    }, format="json")
    assert stale.status_code == 409, stale.data
    change.refresh_from_db()
    assert change.approvals == []


def test_missing_comparison_base_is_explicit(phase5_lease):
    owner, tenant, lease = phase5_lease
    change = RentalChange.objects.create(lease=lease, requester=owner,
        kind="renewal", status="proposed", previous_terms={}, terms=lease.terms)
    result = client_for(tenant).get(f"/api/v1/features/v1/renewals/{change.id}/")
    assert result.status_code == 200, result.data
    assert result.data["comparison"]["base_available"] is False
    assert result.data["comparison"]["base_digest"] == ""
