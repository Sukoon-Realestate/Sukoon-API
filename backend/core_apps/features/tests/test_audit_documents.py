import json
from urllib.parse import urlsplit
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from core_apps.features.models import (
    RentalDocument,
    PaymentReceipt,
    PrivateAccessRevocation,
    RentalTimelineEvent,
)
from core_apps.features.services.private_rental_documents import generate
from core_apps.features.tests.test_rental_phase6 import (
    phase6_lease,
    captured_payment,
    client_for,
)

pytestmark = pytest.mark.django_db


def test_receipt_contains_payment_and_download_serves_exact_private_bytes(phase6_lease):
    owner, tenant, lease = phase6_lease
    _, attempt, _ = captured_payment(lease, tenant)
    receipt = PaymentReceipt.objects.create(payment_attempt=attempt)
    item = RentalDocument.objects.create(
        lease=lease,
        document_type="receipt",
        source_reference=str(receipt.id),
        title="Receipt",
    )
    assert generate(item)
    payload = json.loads(bytes(item.private_content))
    assert payload["receipt_id"] == str(receipt.id)
    assert payload["payment_attempt_id"] == str(attempt.id)
    assert payload["amount_minor"] == attempt.invoice_allocation.amount_minor
    assert "ledger" not in payload
    link = client_for(tenant).get(reverse("rental-document-download", args=[item.id]))
    assert link.status_code == 200
    url = urlsplit(link.data["url"])
    download = APIClient().get(url.path + "?" + url.query)
    assert download.status_code == 200
    assert download.content == bytes(item.private_content)
    assert download["Cache-Control"] == "private, no-store"
    PrivateAccessRevocation.objects.create(lease=lease, user=tenant, reason="Revoked")
    assert APIClient().get(url.path + "?" + url.query).status_code == 404


@pytest.mark.parametrize("kind", ["contract", "change"])
def test_signed_document_is_not_replaced_by_a_statement(phase6_lease, kind):
    _, _, lease = phase6_lease
    item = RentalDocument.objects.create(
        lease=lease, document_type=kind, source_reference="unavailable", title=kind
    )
    assert not generate(item)
    item.refresh_from_db()
    assert item.status == "failed" and not item.private_content
    assert item.failure_code == "signed_source_artifact_unavailable"


def test_rental_center_populates_real_history_and_schedule(phase6_lease):
    _, tenant, lease = phase6_lease
    invoice, _, _ = captured_payment(lease, tenant)
    event = RentalTimelineEvent.objects.create(
        lease=lease, kind="invoice", label="Payment recorded", resource_id=invoice.id
    )
    response = client_for(tenant).get(
        f"/api/v1/features/v1/leases/{lease.id}/rental-center/"
    )
    assert response.status_code == 200
    assert response.data["timeline"][0]["id"] == str(event.id)
    assert response.data["billing_schedule"][0]["invoice_id"] == str(invoice.id)


def test_empty_optional_statement_bounds_remain_unknown_not_invalid_dates(phase6_lease):
    import uuid

    _, tenant, lease = phase6_lease
    response = client_for(tenant).post(
        "/api/v1/features/v1/rental-statements/",
        {
            "lease_id": str(lease.id),
            "expected_revision": lease.revision,
            "request_key": str(uuid.uuid4()),
            "starts_on": "",
            "ends_on_exclusive": "",
        },
        format="json",
    )
    assert response.status_code == 201
    document = RentalDocument.objects.get(id=response.data["resource"]["id"])
    assert document.starts_on is None and document.ends_on_exclusive is None
    assert generate(document)
    payload = json.loads(bytes(document.private_content))
    assert payload["starts_on"] is None and payload["ends_on_exclusive"] is None


@pytest.mark.parametrize(
    "boundary", ["expiry", "logout", "account_epoch", "inactive_account"]
)
def test_issued_private_link_rechecks_expiry_revocation_and_account_authority(
    phase6_lease, monkeypatch, boundary
):
    import time
    from datetime import timedelta
    from django.utils import timezone
    from core_apps.users.models import AuthSession
    from core_apps.features.services import private_rental_documents as documents

    _, tenant, lease = phase6_lease
    session = AuthSession.objects.create(
        user=tenant,
        security_epoch=tenant.security_epoch,
        expires_at=timezone.now() + timedelta(hours=1),
    )
    item = RentalDocument.objects.create(
        lease=lease, document_type="statement", title="Statement"
    )
    assert generate(item)
    client = APIClient()
    client.force_authenticate(tenant, token={"session_id": str(session.id)})
    link = client.get(reverse("rental-document-download", args=[item.id]))
    assert link.status_code == 200
    url = urlsplit(link.data["url"])
    target = url.path + "?" + url.query
    assert APIClient().get(target).status_code == 200
    if boundary == "expiry":
        later = time.time() + 301
        monkeypatch.setattr("django.core.signing.time.time", lambda: later)
    elif boundary == "logout":
        AuthSession.objects.filter(pk=session.pk).update(revoked_at=timezone.now())
    elif boundary == "account_epoch":
        tenant.security_epoch += 1
        tenant.save(update_fields=["security_epoch"])
    else:
        tenant.is_active = False
        tenant.save(update_fields=["is_active"])
    assert APIClient().get(target).status_code == 404
