"""Sending an accepted version for signature preserves the owner's explanation."""

import uuid
from unittest.mock import patch

import pytest
from django.utils import timezone

from core_apps.features.models import RentalChange, RentalConsentRecord, RentalTimelineEvent
from core_apps.features.services.rental_notes import response_note_label
from .test_rental_phase5 import client_for, phase5_lease


@pytest.fixture
def accepted_change(phase5_lease):
    owner, tenant, lease = phase5_lease
    created = client_for(owner).post(
        f"/api/v1/features/v1/leases/{lease.id}/amendments/",
        {
            "reason": "Agreed service change",
            "effective_on": str(timezone.localdate()),
            "terms": {**lease.terms, "included_services": ["Water", "Weekly cleaning"]},
            "evidence_ids": [],
            "lease_revision": lease.revision,
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
        },
        format="json",
    )
    assert created.status_code == 201, created.data
    change = created.data["resource"]
    accepted = client_for(tenant).post(
        f"/api/v1/features/v1/amendments/{change['id']}/respond/",
        {
            "action": "accept",
            "expected_revision": change["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert accepted.status_code == 200, accepted.data
    return owner, tenant, lease, accepted.data["resource"]


def submission(change, note):
    return {
        "action": "submit_for_signature",
        "expected_revision": change["revision"],
        "request_key": str(uuid.uuid4()),
        "note": note,
    }


@pytest.mark.django_db
def test_signature_submission_note_binds_document_and_survives_read_and_replay(accepted_change):
    owner, tenant, lease, change = accepted_change
    endpoint = f"/api/v1/features/v1/amendments/{change['id']}/submit-for-signature/"
    body = submission(change, "  إرسال الشروط التي وافق عليها الطرفان.  ")
    original_terms = lease.terms.copy()
    response = client_for(owner).post(endpoint, body, format="json")
    assert response.status_code == 200, response.data
    resource = response.data["resource"]
    assert resource["status"] == "pending_signatures"
    assert resource["content_revision"] == change["content_revision"]
    record = RentalConsentRecord.objects.get(
        subject_id=change["id"], decision="submit_for_signature", actor=owner,
    )
    assert record.subject_revision == resource["revision"]
    assert record.snapshot["content_version"] == change["content_revision"]
    assert record.snapshot["document_id"] == resource["document_id"]
    assert record.snapshot["document_hash"] == resource["document_hash"]
    assert record.snapshot["terms"] == resource["terms"]
    for actor in (owner, tenant):
        detail = client_for(actor).get(f"/api/v1/features/v1/amendments/{change['id']}/")
        notes = [row for row in detail.data["comments"] if row["action"] == "submit_for_signature"]
        assert len(notes) == 1
        assert notes[0]["note"] == body["note"].strip()
        assert notes[0]["content_version"] == change["content_revision"]
    with patch("core_apps.features.rental_phase5_views_parts.change_signing_session.get_rental_provider") as provider:
        replay = client_for(owner).post(endpoint, body, format="json")
    assert replay.status_code == 200
    assert replay.data == response.data
    provider.assert_not_called()
    assert RentalConsentRecord.objects.filter(subject_id=change["id"], decision="submit_for_signature").count() == 1
    timeline = RentalTimelineEvent.objects.filter(resource_id=change["id"], kind="change_submit_for_signature_note")
    assert timeline.count() == 1
    assert response_note_label(timeline.get(), "ar") == "طلب تعديل العقد: إرسال للتوقيع"
    lease.refresh_from_db()
    assert lease.terms == original_terms
    assert RentalChange.objects.get(id=change["id"]).signed_by == []


@pytest.mark.django_db
@pytest.mark.parametrize("note", [42, "x" * 4001], ids=["not_text", "too_long"])
def test_invalid_submission_note_never_creates_provider_document(accepted_change, note):
    owner, _, _, change = accepted_change
    with patch("core_apps.features.rental_phase5_views_parts.change_signing_session.get_rental_provider") as provider:
        result = client_for(owner).post(
            f"/api/v1/features/v1/amendments/{change['id']}/submit-for-signature/",
            submission(change, note), format="json",
        )
    assert result.status_code == 400
    provider.assert_not_called()
    current = RentalChange.objects.get(id=change["id"])
    assert current.status == "accepted"
    assert current.revision == change["revision"]
    assert not current.document_id
    assert not RentalConsentRecord.objects.filter(subject_id=current.id, decision="submit_for_signature").exists()
