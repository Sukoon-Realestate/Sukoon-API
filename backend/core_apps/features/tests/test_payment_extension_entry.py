"""The invoice exposes the existing participant command without a PSP gate."""
from datetime import timedelta
from unittest.mock import patch
import uuid

import pytest
from django.utils import timezone

from core_apps.features.models import RentalChange
from core_apps.users.models import User
from .test_invoice_read_recovery import overdue_candidate
from .test_rental_phase3 import client_for, phase3_lease


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["tenant", "owner"])
def test_unpaid_participant_can_reach_extension_without_checkout(phase3_lease, role):
    owner, tenant, lease = phase3_lease
    actor = tenant if role == "tenant" else owner
    invoice = overdue_candidate(lease)
    before = (invoice.due_at, invoice.revision, invoice.status)
    client = client_for(actor)
    with patch("core_apps.features.providers.checkout_available", return_value=False):
        response = client.get(f"/api/v1/features/v1/rent-invoices/{invoice.id}/")
    assert response.status_code == 200
    assert response.data["can_pay"] is False
    assert "request_extension" in response.data["allowed_actions"]
    result = client.post(
        f"/api/v1/features/v1/leases/{lease.id}/payment-extension-requests/",
        {"invoice_id": str(invoice.id), "lease_revision": lease.revision,
         "expected_revision": 0, "request_key": str(uuid.uuid4()),
         "requested_date": str(timezone.localdate()+timedelta(days=3)),
         "reason": "Synthetic extension review", "evidence_ids": []}, format="json",
    )
    assert result.status_code == 201, result.data
    assert RentalChange.objects.filter(lease=lease, invoice=invoice, kind="payment_extension").count() == 1
    invoice.refresh_from_db()
    assert (invoice.due_at, invoice.revision, invoice.status) == before
    assert invoice.deferred_until is None


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["paid", "settled", "cancelled", "written_off"])
def test_closed_invoice_exposes_no_extension(phase3_lease, status):
    _, tenant, lease = phase3_lease
    invoice = overdue_candidate(lease)
    invoice.status = status
    invoice.save(update_fields=["status"])
    response = client_for(tenant).get(f"/api/v1/features/v1/rent-invoices/{invoice.id}/")
    assert response.status_code == 200
    assert "request_extension" not in response.data["allowed_actions"]


@pytest.mark.django_db
def test_legacy_and_unrelated_readers_do_not_gain_extension(phase3_lease):
    _, tenant, lease = phase3_lease
    invoice = overdue_candidate(lease)
    outsider = User.objects.create_user(email="extension-outsider@example.test", is_verified=True)
    path = f"/api/v1/features/v1/rent-invoices/{invoice.id}/"
    assert client_for(outsider).get(path).status_code == 404
    lease.legacy_read_only = True
    lease.save(update_fields=["legacy_read_only"])
    response = client_for(tenant).get(path)
    assert response.status_code == 200
    assert "request_extension" not in response.data["allowed_actions"]
