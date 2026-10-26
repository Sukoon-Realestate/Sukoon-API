"""Provider-contract tests with explicit mocked transport, never provider evidence."""

import copy
import hashlib
import hmac
import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
import requests
from django.db import transaction
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.exceptions import PermissionDenied

from core_apps.features.models import (
    ChangeSigningSession,
    RentalChange,
    RentalDocument,
    RentalOperationalCase,
    RentalSigningDocument,
    RentalSigningHint,
    SigningSession,
)
from core_apps.features.services import signwell_client, signing_documents, signing_jobs
from core_apps.features.services.rental_phase2 import (
    RentalConflict,
    reserve_inventory_days,
)
from core_apps.features.services.rental_lifecycle.inventory import expire_property_holds
from core_apps.features.rental_phase2_views_parts.apply_fake_rental_event import (
    apply_fake_rental_event,
)
from . import test_rental_phase5 as fixtures
from .test_rental_phase5 import client_for

phase5_lease = fixtures.phase5_lease

pytestmark = pytest.mark.django_db
API = "/api/v1/features/v1/"
PDF = b"%PDF-1.7\nfixture original with provider audit\n%%EOF"


@pytest.fixture
def signing_source(phase5_lease, settings):
    settings.SIGNWELL_TEST_ENABLED = True
    settings.SIGNWELL_API_KEY = "test-only-key"
    settings.SIGNWELL_WEBHOOK_ID = "synthetic-webhook"
    settings.RENTAL_RUNTIME_ENVIRONMENT = "test"
    owner, tenant, lease = phase5_lease
    change = RentalChange.objects.create(
        lease=lease,
        requester=owner,
        kind="amendment",
        status="accepted",
        terms=lease.terms,
        previous_terms=lease.terms,
        approvals=[str(owner.id), str(tenant.id)],
    )
    result = signing_documents.prepare(change.id, change.revision, change.terms)
    change.document_id, change.document_hash = result.document_id, result.digest
    change.status = "pending_signatures"
    change.revision += 1
    change.save()
    return (
        owner,
        tenant,
        lease,
        change,
        RentalSigningDocument.objects.get(id=result.document_id),
    )


def fact(document, status="pending"):
    return {
        "id": str(document.provider_document_id or uuid.uuid4()),
        "test_mode": True,
        "status": status,
        "metadata": {
            "sokoun_document_id": str(document.id),
            "sokoun_source_hash": document.source_hash,
        },
        "recipients": [
            {
                **value,
                "embedded_signing_url": f"https://www.signwell.com/docs/{value['id']}",
            }
            for value in document.recipients
        ],
    }


def due(document):
    RentalSigningDocument.objects.filter(pk=document.pk).update(
        next_check_at=None, claimed_at=None
    )
    document.refresh_from_db()


def send(document):
    with patch.object(signwell_client, "create", return_value=fact(document)) as create:
        assert signing_jobs.run(document.id) == "pending"
        create.assert_called_once()
    document.refresh_from_db()


def sessions(source):
    owner, tenant, lease, change, document = source
    rows = []
    for actor in (owner, tenant):
        key = uuid.uuid4()
        hosted = signing_documents.hosted_session(change.id, actor.id, key)
        rows.append(
            ChangeSigningSession.objects.create(
                change=change,
                signer=actor,
                request_key=key,
                change_revision=change.revision,
                document_id=document.id,
                document_hash=document.source_hash,
                provider_session_id=hosted.provider_session_id,
                hosted_url=hosted.hosted_url,
                expires_at=timezone.now() + timedelta(minutes=30),
            )
        )
    return rows


def complete(document):
    due(document)
    with patch.object(
        signwell_client, "retrieve", return_value=fact(document, "completed")
    ), patch.object(signwell_client, "completed_pdf", return_value=PDF):
        return signing_jobs.run(document.id)


def test_frozen_source_and_no_network_inside_preparation(signing_source):
    _, _, lease, change, document = signing_source
    assert document.status == "prepared" and not document.provider_document_id
    assert (
        document.source_hash
        == hashlib.sha256(bytes(document.source_content)).hexdigest()
    )
    assert "عقد الإيجار" in bytes(document.source_content).decode()
    lease.terms = {**lease.terms, "included_services": ["New listing terms"]}
    lease.save()
    document.refresh_from_db()
    assert document.snapshot["terms"]["included_services"] == []
    with pytest.raises(RentalConflict):
        signing_documents.prepare(change.id, change.revision - 1, change.terms)


def test_success_retains_exact_pdf_and_applies_change_once(signing_source):
    _, _, lease, change, document = signing_source
    send(document)
    rows = sessions(signing_source)
    assert complete(document) == "applied"
    change.refresh_from_db()
    lease.refresh_from_db()
    assert change.status == "signed" and lease.status == "active"
    artifact = RentalDocument.objects.get(lease=lease, source_reference=str(change.id))
    assert artifact.status == "ready" and artifact.media_type == "application/pdf"
    assert bytes(artifact.private_content) == PDF
    assert artifact.sha256 == hashlib.sha256(PDF).hexdigest()
    assert all(
        ChangeSigningSession.objects.get(pk=row.pk).status == "completed"
        for row in rows
    )
    revision = change.revision
    with patch.object(signwell_client, "create") as create, patch.object(
        signwell_client, "retrieve"
    ) as retrieve:
        assert signing_jobs.run(document.id) == "waiting"
        assert signing_jobs.apply(document.id) == "applied"
        create.assert_not_called()
        retrieve.assert_not_called()
    change.refresh_from_db()
    assert (
        change.revision == revision
        and RentalDocument.objects.filter(lease=lease).count() == 1
    )


def test_lost_create_reply_never_reposts_and_verified_hint_restores_original(
    signing_source,
):
    *_, document = signing_source
    with patch.object(
        signwell_client,
        "create",
        side_effect=signwell_client.SigningTransportError(
            "creation_result_unknown", uncertain=True
        ),
    ) as create:
        assert signing_jobs.run(document.id) == "unknown"
        due(document)
        assert signing_jobs.run(document.id) == "unknown"
        assert create.call_count == 1
    result = fact(document)
    event = {"type": "document_created", "time": int(timezone.now().timestamp())}
    event["hash"] = hmac.new(
        b"synthetic-webhook",
        f"{event['type']}@{event['time']}".encode(),
        hashlib.sha256,
    ).hexdigest()
    hook = APIClient().post(
        API + "signing/provider-events/",
        {"event": event, "data": {"object": result}},
        format="json",
    )
    assert hook.status_code == 202
    document.refresh_from_db()
    assert document.provider_document_id is None and document.status == "unknown"
    with patch.object(signwell_client, "create") as create, patch.object(
        signwell_client, "retrieve", return_value=result
    ):
        assert signing_jobs.run(document.id) == "pending"
        create.assert_not_called()
    document.refresh_from_db()
    assert str(document.provider_document_id) == result["id"]


def test_unknown_webhook_is_hint_only_and_mismatched_document_cannot_sign(
    signing_source,
):
    *_, document = signing_source
    RentalSigningDocument.objects.filter(pk=document.pk).update(status="unknown")
    result = fact(document, "completed")
    result["metadata"]["sokoun_source_hash"] = "wrong"
    RentalSigningHint.objects.create(
        document=document, provider_document_id=result["id"]
    )
    with patch.object(signwell_client, "retrieve", return_value=result), patch.object(
        signwell_client, "completed_pdf"
    ) as pdf:
        assert signing_jobs.run(document.id) == "unknown"
        pdf.assert_not_called()
    document.refresh_from_db()
    assert document.provider_document_id is None and not document.completed_hash


@pytest.mark.parametrize(
    "field", ["test_mode", "recipient", "metadata", "url", "duplicate"]
)
def test_authenticated_provider_response_must_match_frozen_parties(
    signing_source, field
):
    *_, document = signing_source
    result = fact(document)
    if field == "test_mode":
        result[field] = False
    elif field == "recipient":
        result["recipients"][0]["email"] = "outsider@example.test"
    elif field == "metadata":
        result[field]["sokoun_document_id"] = str(uuid.uuid4())
    elif field == "url":
        result["recipients"][0][
            "embedded_signing_url"
        ] = "https://attacker.example/sign"
    else:
        result["recipients"].append(copy.deepcopy(result["recipients"][0]))
    with pytest.raises(
        signwell_client.SigningTransportError, match="signing_document_mismatch"
    ):
        signwell_client.verified(document, result)


def test_pdf_processing_retries_get_and_never_creates_new_document(signing_source):
    *_, document = signing_source
    send(document)
    sessions(signing_source)
    due(document)
    with patch.object(
        signwell_client, "retrieve", return_value=fact(document, "completed")
    ), patch.object(
        signwell_client,
        "completed_pdf",
        side_effect=signwell_client.SigningTransportError("signed_pdf_processing"),
    ):
        assert signing_jobs.run(document.id) == "waiting"
    document.refresh_from_db()
    assert document.provider_document_id and document.status == "awaiting_pdf"
    assert not RentalDocument.objects.filter(status="ready").exists()
    with patch.object(signwell_client, "create") as create:
        assert complete(document) == "applied"
        create.assert_not_called()


def test_changed_source_preserves_signed_original_and_one_review_case(signing_source):
    *_, change, document = signing_source
    send(document)
    sessions(signing_source)
    change.document_hash = "changed"
    change.save()
    assert complete(document) == "review_required"
    assert complete(document) == "waiting"
    assert (
        RentalOperationalCase.objects.filter(
            source_key=f"signwell:{document.id}"
        ).count()
        == 1
    )
    assert (
        bytes(
            RentalDocument.objects.get(source_reference=str(change.id)).private_content
        )
        == PDF
    )
    change.refresh_from_db()
    assert change.status == "pending_signatures"


def test_mock_completion_cannot_assert_real_signature(signing_source):
    *_, document = signing_source
    send(document)
    row = sessions(signing_source)[0]
    with pytest.raises(PermissionDenied):
        apply_fake_rental_event(
            {
                "type": "change-signature.completed",
                "provider_session_id": row.provider_session_id,
            }
        )
    row.refresh_from_db()
    assert row.status == "pending"


def test_session_descriptor_tracks_original_provider_not_current_configuration(signing_source, settings):
    from core_apps.features.providers import mock_completion_metadata
    *_, document = signing_source
    send(document)
    row = sessions(signing_source)[0]
    settings.SIGNWELL_TEST_ENABLED = False
    result = mock_completion_metadata("change-signing-sessions", row.id, 1)
    assert result["provider_mode"] == "hosted" and "mock_completion" not in result
    row.document_id = uuid.uuid4(); row.save()
    settings.SIGNWELL_TEST_ENABLED = True
    assert mock_completion_metadata("change-signing-sessions", row.id, 1)["provider_mode"] == "mock"


def test_status_access_and_old_identity_never_resolves_replacement(signing_source):
    owner, tenant, _, change, document = signing_source
    path = API + f"signing/documents/{document.id}/"
    assert APIClient().get(path).status_code == 401
    response = client_for(owner).get(path)
    assert response.status_code == 200 and response.data["id"] == str(document.id)
    assert (
        "provider_result" not in response.data and "source_content" not in response.data
    )
    change.document_id = uuid.uuid4()
    change.save()
    assert client_for(tenant).get(path).data["id"] == str(document.id)


def test_worker_crash_after_send_is_unknown_not_another_post(signing_source):
    *_, document = signing_source
    RentalSigningDocument.objects.filter(pk=document.pk).update(
        status="requesting", claimed_at=timezone.now() - timedelta(minutes=3)
    )
    with patch.object(signwell_client, "create") as create:
        assert signing_jobs.run(document.id) == "unknown"
        create.assert_not_called()
    document.refresh_from_db()
    assert document.status == "unknown"


def test_hold_and_session_expiry_cannot_erase_unknown_signature(signing_source):
    owner, tenant, lease, _, _ = signing_source
    lease.status = "draft"
    lease.start_date = timezone.localdate() + timedelta(days=1)
    lease.end_date = lease.start_date + timedelta(days=2)
    lease.offer_snapshot = {"rental_scope": "entire_property"}
    lease.hold_expires_at = timezone.now() + timedelta(minutes=1)
    lease.save()
    with transaction.atomic():
        reserve_inventory_days(
            lease, lease.start_date, lease.end_date, lease.hold_expires_at
        )
    generated = signing_documents.prepare(lease.id, lease.revision, lease.terms)
    document = RentalSigningDocument.objects.get(id=generated.document_id)
    document.status = "unknown"
    document.save()
    lease.document_id, lease.document_hash = document.id, document.source_hash
    lease.status = "pending_signatures"
    lease.save()
    lease.inventory_day_locks.update(expires_at=timezone.now() - timedelta(minutes=1))
    with transaction.atomic():
        expire_property_holds(lease.property)
    lease.refresh_from_db()
    assert (
        lease.status == "pending_signatures" and lease.inventory_day_locks.count() == 2
    )
    session = SigningSession.objects.create(
        lease=lease,
        signer=owner,
        request_key=uuid.uuid4(),
        document_id=document.id,
        document_hash=document.source_hash,
        lease_revision=lease.revision,
        expires_at=timezone.now() - timedelta(minutes=1),
        provider_session_id=str(uuid.uuid4()),
    )
    from core_apps.features.tasks_parts.expire_rental_sources_and_holds import (
        reconcile_rental_provider_sessions,
    )

    reconcile_rental_provider_sessions()
    session.refresh_from_db()
    assert session.status == "pending"


def test_transport_is_test_only_bounded_and_does_not_retry_unknown(signing_source):
    *_, document = signing_source
    with patch.object(requests, "request", side_effect=requests.Timeout) as request:
        with pytest.raises(signwell_client.SigningTransportError) as error:
            signwell_client.create(document)
        assert error.value.uncertain is True and request.call_count == 1
    kwargs = request.call_args.kwargs
    assert kwargs["headers"]["X-TestMode-Enabled"] == "true"
    assert kwargs["json"]["test_mode"] is True
    assert kwargs["json"]["allow_reassign"] is False
    assert kwargs["json"]["embedded_signing_notifications"] is False
    assert kwargs["allow_redirects"] is False


def test_production_environment_never_uses_test_signing(signing_source, settings):
    settings.RENTAL_RUNTIME_ENVIRONMENT = "production"
    assert signwell_client.ready() is False
    with patch.object(requests, "request") as request:
        assert signing_jobs.run(signing_source[-1].id) == "unavailable"
        request.assert_not_called()


def test_unsigned_webhook_cannot_queue_document_work(signing_source):
    *_, document = signing_source
    response = APIClient().post(
        API + "signing/provider-events/",
        {"data": {"object": fact(document, "completed")}},
        format="json",
    )
    assert response.status_code == 403
    assert document.hints.count() == 0
    assert not signwell_client.verify_event(
        {"event": {"type": "document_completed", "time": 1, "hash": "0" * 64}}
    )


def test_unconfigured_webhook_keeps_new_creation_unavailable(signing_source, settings):
    settings.SIGNWELL_WEBHOOK_ID = ""
    assert signwell_client.ready() is False
    with patch.object(signwell_client, "create") as create:
        assert signing_jobs.run(signing_source[-1].id) == "unavailable"
        create.assert_not_called()


def test_draft_or_unrecognized_provider_status_does_not_enable_signing(signing_source):
    *_, document = signing_source
    with patch.object(signwell_client, "create", return_value=fact(document, "Draft")):
        assert signing_jobs.run(document.id) == "unknown"
    document.refresh_from_db()
    assert (
        document.provider_document_id
        and not signing_documents.current_provider_read(document)
    )


def test_original_lease_completes_signing_and_issues_existing_initial_invoice(
    signing_source,
):
    owner, tenant, lease, _, _ = signing_source
    from .test_rental_phase2 import agreement_terms

    lease.status = "draft"
    lease.start_date = timezone.localdate() + timedelta(days=10)
    lease.end_date = lease.start_date + timedelta(days=31)
    lease.terms = agreement_terms(lease.start_date, lease.end_date)
    lease.offer_snapshot = {"rental_scope": "entire_property"}
    lease.hold_expires_at = timezone.now() + timedelta(hours=1)
    lease.save()
    with transaction.atomic():
        reserve_inventory_days(
            lease, lease.start_date, lease.end_date, lease.hold_expires_at
        )
    generated = signing_documents.prepare(lease.id, lease.revision, lease.terms)
    document = RentalSigningDocument.objects.get(id=generated.document_id)
    lease.document_id, lease.document_hash = document.id, document.source_hash
    lease.status = "pending_signatures"
    lease.revision += 1
    lease.save()
    send(document)
    for actor in (owner, tenant):
        key = uuid.uuid4()
        result = client_for(actor).post(
            API + f"leases/{lease.id}/signing-session/",
            {
                "request_key": str(key),
                "expected_revision": lease.revision,
                "document_id": str(document.id),
                "document_hash": document.source_hash,
            },
            format="json",
        )
        assert result.status_code == 201, result.data
        assert (
            result.data["provider_mode"] == "hosted"
            and "mock_completion" not in result.data
        )
    assert complete(document) == "applied"
    lease.refresh_from_db()
    assert lease.status == "signed" and lease.invoices.count() == 1
    assert lease.inventory_day_locks.filter(kind="hold").count() == 31
    original = RentalDocument.objects.get(lease=lease, document_type="contract")
    assert bytes(original.private_content) == PDF
    result = client_for(tenant).get(API + f"rental-documents/{original.id}/download/")
    assert result.status_code == 200, result.data
    response = APIClient().get(result.data["url"])
    assert response.status_code == 200 and response.content == PDF
    assert (
        response["Content-Type"] == "application/pdf"
        and ".pdf" in response["Content-Disposition"]
    )


def test_changed_frozen_terms_cannot_send_a_document(signing_source):
    *_, change, document = signing_source
    change.terms = {**change.terms, "included_services": ["Unreviewed"]}
    change.save()
    with patch.object(signwell_client, "create") as create:
        assert signing_jobs.run(document.id) == "waiting"
        create.assert_not_called()
    document.refresh_from_db()
    assert document.status == "closed"


def test_reconcile_command_is_versioned_and_idempotent_without_sending(signing_source):
    owner, _, _, _, document = signing_source
    document.status = "failed"
    document.save()
    key = str(uuid.uuid4())
    body = {"expected_status": "failed", "source_hash": document.source_hash}
    path = API + f"signing/documents/{document.id}/"
    with patch.object(signwell_client, "create") as create:
        first = client_for(owner).post(
            path, body, format="json", HTTP_IDEMPOTENCY_KEY=key
        )
        assert first.status_code == 200, first.data
        replay = client_for(owner).post(
            path, body, format="json", HTTP_IDEMPOTENCY_KEY=key
        )
        assert replay.status_code == 200 and replay.data == first.data
        create.assert_not_called()
    assert (
        client_for(owner)
        .post(path, body, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        .status_code
        == 409
    )


def test_stale_provider_read_cannot_open_a_new_local_signing_session(signing_source):
    owner, _, _, change, document = signing_source
    send(document)
    result = document.provider_result
    result["checked_at"] = (timezone.now() - timedelta(hours=2)).isoformat()
    document.provider_result = result
    document.save()
    assert signing_documents.document_projection(document, owner)["can_open"] is False
    with pytest.raises(RentalConflict):
        signing_documents.hosted_session(change.id, owner.id, uuid.uuid4())


def test_suspended_party_retains_original_but_cannot_apply_signature(signing_source):
    owner, _, _, change, document = signing_source
    send(document)
    sessions(signing_source)
    owner.is_active = False
    owner.save()
    assert complete(document) == "review_required"
    assert RentalDocument.objects.get(source_reference=str(change.id)).status == "ready"


def test_explicit_recheck_applies_retained_original_without_another_provider_call(
    signing_source, settings
):
    owner, tenant, _, change, document = signing_source
    send(document)
    sessions(signing_source)
    owner.is_active = False
    owner.save()
    assert complete(document) == "review_required"
    owner.is_active = True
    owner.save()
    settings.SIGNWELL_API_KEY = ""
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    body = {"expected_status": "review_required", "source_hash": document.source_hash}
    result = client_for(tenant).post(
        API + f"signing/documents/{document.id}/",
        body,
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )
    assert result.status_code == 200, result.data
    with patch.object(signwell_client, "create") as create, patch.object(
        signwell_client, "retrieve"
    ) as retrieve:
        assert signing_jobs.run(document.id) == "applied"
        create.assert_not_called()
        retrieve.assert_not_called()
    change.refresh_from_db()
    assert change.status == "signed"


def test_retry_permission_is_not_disclosed_to_a_different_person(signing_source):
    owner, tenant, _, _, document = signing_source
    document.status = "failed"
    document.save()
    assert signing_documents.document_projection(document, owner)["can_retry"]
    assert signing_documents.document_projection(document, tenant)["can_retry"]
    from core_apps.users.models import User

    outsider = User.objects.create_user(
        email="signature-outsider@example.test", password="synthetic", is_verified=True
    )
    assert not signing_documents.document_projection(document, outsider)["can_retry"]
    assert (
        client_for(outsider).get(API + f"signing/documents/{document.id}/").status_code
        == 404
    )


@pytest.mark.django_db(transaction=True)
def test_competing_workers_send_only_one_original(signing_source):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from django.db import connections

    *_, document = signing_source
    entered, release = Event(), Event()

    def provider(_):
        entered.set()
        assert release.wait(10)
        return fact(document)

    def run():
        connections.close_all()
        try:
            return signing_jobs.run(document.id)
        finally:
            connections.close_all()

    with patch.object(
        signwell_client, "create", side_effect=provider
    ) as create, ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(run)
        try:
            assert entered.wait(10)
            assert pool.submit(run).result(10) == "waiting"
        finally:
            release.set()
        assert first.result(10) == "pending"
        assert create.call_count == 1
