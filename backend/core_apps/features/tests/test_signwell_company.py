"""Company signing uses the same provider facts and current mandate rules."""

from unittest.mock import patch
from datetime import timedelta
import pytest
from django.utils import timezone
from core_apps.features.models import RentalSigningDocument, RentalDocument
from core_apps.features.services import signwell_client, signing_jobs
from core_apps.features.services.company.tenancy_expiry import expire
from . import test_company_tenancy as fixtures
from .test_company_tenancy import act, authenticated, API

agreement = fixtures.agreement
cycle = fixtures.cycle
company_setup = fixtures.company_setup
rental_participants = fixtures.rental_participants
policy = fixtures.policy
from .test_signwell_documents import send, complete

pytestmark = pytest.mark.django_db


@pytest.fixture
def provider_company(agreement, settings):
    settings.SIGNWELL_TEST_ENABLED = True
    settings.SIGNWELL_API_KEY = "test-only-key"
    settings.SIGNWELL_WEBHOOK_ID = "synthetic-webhook"
    settings.RENTAL_RUNTIME_ENVIRONMENT = "test"
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    cycle, item, _, _ = agreement
    for role in ["owner", "signer"]:
        response = act(item, cycle[role], "review", role=role, digest=item.terms_digest)
        assert response.status_code == 200, response.data
    response = act(item, cycle["owner"], "submit_signature")
    assert response.status_code == 200, response.data
    item.lease.refresh_from_db()
    document = RentalSigningDocument.objects.get(id=item.lease.document_id)
    return cycle, item, document


def test_real_company_document_completes_both_signers_and_retains_pdf(provider_company):
    cycle, item, document = provider_company
    assert {row["id"] for row in document.recipients} == {
        str(cycle["owner"].id),
        str(cycle["signer"].id),
    }
    send(document)
    for role in ["owner", "signer"]:
        response = act(item, cycle[role], "sign", digest=item.lease.document_hash)
        assert response.status_code == 200, response.data
        detail = authenticated(cycle[role]).get(API + f"company-tenancies/{item.id}/")
        session = detail.data["signing_sessions"][0]
        assert session["provider_mode"] == "hosted" and "mock_completion" not in session
    assert complete(document) == "applied"
    item.lease.refresh_from_db()
    assert item.lease.status == "signed" and item.lease.invoices.count() == 1
    assert (
        RentalDocument.objects.get(
            lease=item.lease, document_type="contract"
        ).media_type
        == "application/pdf"
    )
    employee = authenticated(cycle["employee"]).get(
        API + f"company-tenancies/{item.id}/"
    )
    assert employee.status_code == 200
    assert employee.data["active_role"] == "employee"
    assert {"signing_document", "signing_sessions", "document_hash", "terms"}.isdisjoint(employee.data)
    assert (
        authenticated(cycle["employee"])
        .get(API + f"signing/documents/{document.id}/")
        .status_code
        == 404
    )


def test_unknown_creation_before_sessions_protects_company_inventory(provider_company):
    cycle, item, document = provider_company
    with patch.object(
        signwell_client,
        "create",
        side_effect=signwell_client.SigningTransportError("unknown", uncertain=True),
    ):
        assert signing_jobs.run(document.id) == "unknown"
    item.lease.hold_expires_at = timezone.now() - timedelta(minutes=1)
    item.lease.save()
    assert expire(item) is False
    assert item.lease.inventory_day_locks.exists()
    response = act(item, cycle["owner"], "cancel", reason="Try to discard the original")
    assert response.status_code in {403, 409}


def test_revoked_signer_cannot_open_provider_document(provider_company):
    cycle, item, document = provider_company
    send(document)
    mandate = item.signer_mandate
    mandate.state = "revoked"
    mandate.save()
    response = act(item, cycle["signer"], "sign", digest=item.lease.document_hash)
    assert response.status_code == 404
    assert not item.lease.signing_sessions.exists()


def test_expired_local_link_resumes_same_company_provider_document(provider_company):
    cycle, item, document = provider_company
    send(document)
    response = act(item, cycle["owner"], "sign", digest=item.lease.document_hash)
    assert response.status_code == 200, response.data
    session = item.lease.signing_sessions.get(signer=cycle["owner"])
    original = session.provider_session_id
    session.expires_at = timezone.now() - timedelta(minutes=1)
    session.save()
    with patch.object(signwell_client, "create") as create:
        response = act(item, cycle["owner"], "sign", digest=item.lease.document_hash)
        assert response.status_code == 200, response.data
        create.assert_not_called()
    session.refresh_from_db()
    assert (
        session.provider_session_id == original and session.expires_at > timezone.now()
    )
    assert item.lease.signing_sessions.count() == 1
