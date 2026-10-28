"""A concurrent amendment cannot silently replace a newer signed lease."""

from copy import deepcopy
from datetime import timedelta
from unittest.mock import patch
import uuid

import pytest
from django.utils import timezone

from core_apps.features.models import ChangeSigningSession, RentalChange, RentalOperationalCase
from core_apps.features.rental_phase5_views_parts.change_signing_session import complete_change_signature
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.tasks import process_rental_changes
from .test_rental_phase5 import client_for, phase5_lease


def competing_change(lease, owner, status):
    previous = deepcopy(lease.terms)
    item = RentalChange.objects.create(
        lease=lease, requester=owner, kind=RentalChange.Kind.AMENDMENT,
        status=status, previous_terms=previous,
        terms={**previous, "included_services": ["Old proposal services"]},
        approvals=[str(owner.id), str(lease.tenant.id)],
        effective_on=timezone.localdate(),
        document_id=uuid.uuid4() if status != "accepted" else None,
        document_hash="a" * 64 if status != "accepted" else "",
    )
    # This fixture represents a different, already applied amendment.
    lease.terms = {**previous, "included_services": ["Current agreed services"]}
    lease.revision += 1
    lease.save(update_fields=["terms", "revision"])
    return item


@pytest.mark.django_db
@pytest.mark.parametrize("stage", ["accepted", "pending_signatures"])
def test_changed_base_blocks_submission_and_new_signing_session(phase5_lease, stage):
    owner, tenant, lease = phase5_lease
    item = competing_change(lease, owner, stage)
    actor = owner if stage == "accepted" else tenant
    endpoint = "submit-for-signature" if stage == "accepted" else "signing-session"
    payload = {"request_key": str(uuid.uuid4()), "expected_revision": item.revision,
               "document_id": str(item.document_id), "document_hash": item.document_hash}
    with patch("core_apps.features.rental_phase5_views_parts.change_signing_session.get_rental_provider") as provider:
        response = client_for(actor).post(
            f"/api/v1/features/v1/amendments/{item.id}/{endpoint}/", payload, format="json",
        )
    assert response.status_code == 409, response.data
    provider.assert_not_called()
    original_revision = item.revision
    item.refresh_from_db()
    assert item.status == stage and item.revision == original_revision
    assert not item.signing_sessions.exists()
    detail = client_for(actor).get(f"/api/v1/features/v1/amendments/{item.id}/")
    assert detail.data["allowed_actions"] == []
    assert detail.data["blocking_reasons"]


@pytest.mark.django_db
def test_existing_session_cannot_complete_after_base_changes(phase5_lease):
    owner, tenant, lease = phase5_lease
    item = competing_change(lease, owner, "pending_signatures")
    session = ChangeSigningSession.objects.create(
        change=item, signer=tenant, request_key=uuid.uuid4(),
        change_revision=item.revision, document_id=item.document_id,
        document_hash=item.document_hash, provider_session_id="old-base-session",
        hosted_url="https://example.invalid/sign", expires_at=timezone.now()+timedelta(minutes=10),
    )
    with pytest.raises(RentalConflict) as error:
        complete_change_signature(session.provider_session_id)
    assert error.value.get_codes() == "lease_terms_changed"
    session.refresh_from_db()
    item.refresh_from_db()
    assert session.status == "pending" and session.completed_at is None
    assert item.status == "pending_signatures" and item.signed_by == []


@pytest.mark.django_db
def test_worker_preserves_conflicting_signed_change_and_processes_valid_change_once(phase5_lease):
    owner, _, lease = phase5_lease
    stale = competing_change(lease, owner, "signed")
    old_document, old_terms = stale.document_id, deepcopy(stale.terms)
    current = RentalChange.objects.create(
        lease=lease, requester=owner, kind=RentalChange.Kind.AMENDMENT, status="signed",
        previous_terms=deepcopy(lease.terms),
        terms={**lease.terms, "included_services": ["Latest agreed services"]},
        effective_on=timezone.localdate(), document_id=uuid.uuid4(), document_hash="b"*64,
    )
    lease_revision = lease.revision
    assert process_rental_changes()["applied"] == 1
    assert process_rental_changes()["applied"] == 0
    lease.refresh_from_db()
    stale.refresh_from_db()
    current.refresh_from_db()
    assert lease.terms == current.terms and lease.revision == lease_revision+1
    assert current.status == "applied"
    assert stale.status == "signed" and stale.applied_at is None
    assert stale.document_id == old_document and stale.terms == old_terms
    assert RentalOperationalCase.objects.filter(
        kind="agreement_terms_review", source_key=f"change-terms:{stale.id}:{stale.revision}",
    ).count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("language,expected", [
    ("ar", "تغيرت شروط العقد. راجع الاتفاق الحالي قبل توقيع مقترح جديد."),
    ("en", "The lease terms changed. Review the current agreement before signing a new proposal."),
])
def test_base_conflict_reason_uses_requested_language_without_rewriting_user_text(phase5_lease, language, expected):
    owner, tenant, lease = phase5_lease
    item = competing_change(lease, owner, "pending_signatures")
    item.reason = "Original participant text remains unchanged"
    item.save(update_fields=["reason"])
    response = client_for(tenant).get(
        f"/api/v1/features/v1/amendments/{item.id}/", HTTP_ACCEPT_LANGUAGE=language,
    )
    assert response.status_code == 200
    assert response.data["blocking_reasons"] == [expected]
    assert response.data["reason"] == item.reason
    assert response.data["allowed_actions"] == []
    assert response["Content-Language"] == language
