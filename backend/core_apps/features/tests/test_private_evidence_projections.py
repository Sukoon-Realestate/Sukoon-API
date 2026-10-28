"""Participant attachment cards retain the metadata needed for private viewing."""

import uuid

import pytest
from django.utils import timezone

from core_apps.features.models import MaintenanceRequest, RentalDispute, RentalEvidence
from core_apps.users.models import User
from .test_rental_phase5 import client_for, phase5_lease


@pytest.fixture
def attachment(phase5_lease):
    _, tenant, lease = phase5_lease
    return RentalEvidence.objects.create(
        lease=lease, uploader=tenant, request_key=uuid.uuid4(), original_name="synthetic.png",
        content_type="image/png", size_bytes=42, sha256="a" * 64,
        storage_key=f"test/{uuid.uuid4()}", malware_status="safe", revision=2,
        media_metadata={"kind": "image", "width": 4, "height": 4},
    )


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["maintenance", "dispute"])
def test_participants_receive_complete_current_metadata_but_outsiders_cannot_read(phase5_lease, attachment, kind):
    owner, tenant, lease = phase5_lease
    if kind == "maintenance":
        item = MaintenanceRequest.objects.create(
            lease=lease, reporter=tenant, title="Synthetic request", description="Test only",
            category="water", priority="normal",
        )
        route = "maintenance-requests"
    else:
        item = RentalDispute.objects.create(
            lease=lease, opened_by=tenant, subject_kind="lease", subject_id=lease.id,
            reason="Synthetic dispute",
        )
        route = "disputes"
    item.evidence.add(attachment)
    path = f"/api/v1/features/v1/{route}/{item.id}/"
    for actor in (owner, tenant):
        response = client_for(actor).get(path)
        assert response.status_code == 200, response.data
        evidence = response.data["evidence"]
        assert len(evidence) == 1
        assert evidence[0] == {
            "id": str(attachment.id), "lease_id": str(lease.id), "name": "synthetic.png",
            "mime_type": "image/png", "size_bytes": 42, "sha256": "a" * 64,
            "revision": 2, "status": "ready", "media_metadata": attachment.media_metadata,
        }
    outsider = User.objects.create_user(email="outside-evidence@example.test", password="test-only", is_verified=True)
    assert client_for(outsider).get(path).status_code == 404
    attachment.malware_status = "unsafe"
    attachment.revision += 1
    attachment.save(update_fields=["malware_status", "revision"])
    current = client_for(tenant).get(path).data["evidence"][0]
    assert current["status"] == "unsafe" and current["revision"] == 3
    attachment.deleted_at = timezone.now()
    attachment.save(update_fields=["deleted_at"])
    assert client_for(tenant).get(path).data["evidence"] == []
    assert item.evidence.count() == 1  # Preserve the historical relationship.


@pytest.mark.django_db
def test_new_request_cannot_attach_deleted_evidence(phase5_lease, attachment):
    _, tenant, lease = phase5_lease
    attachment.deleted_at = timezone.now()
    attachment.save(update_fields=["deleted_at"])
    result = client_for(tenant).post(
        f"/api/v1/features/v1/leases/{lease.id}/maintenance-requests/",
        {"title": "Synthetic request", "description": "Test only", "category": "water",
         "priority": "normal", "access_times": ["By agreement"],
         "evidence_ids": [str(attachment.id)], "request_key": str(uuid.uuid4()), "expected_revision": 0},
        format="json",
    )
    assert result.status_code == 400
    assert not lease.maintenance_requests.exists()
