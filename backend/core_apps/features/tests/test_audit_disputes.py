import uuid
from unittest.mock import patch
import pytest
from django.urls import reverse
from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import (
    RentalDispute,
    PrivateAccessRevocation,
    IdempotencyRecord,
    RentInvoice,
)
from core_apps.features.tests.test_rental_phase6 import phase6_lease, client_for

pytestmark = pytest.mark.django_db


def dispute(lease, tenant, status="open"):
    return RentalDispute.objects.create(
        lease=lease,
        opened_by=tenant,
        subject_kind="invoice",
        subject_id=uuid.uuid4(),
        status=status,
    )


@pytest.mark.parametrize("action", ["reply", "resolve", "reject"])
def test_terminal_dispute_is_immutable(phase6_lease, superuser, action):
    owner, tenant, lease = phase6_lease
    item = dispute(lease, tenant, status="resolved")
    actor = tenant if action == "reply" else superuser
    response = client_for(actor).post(
        reverse("rental-dispute-respond", args=[item.id]),
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": item.revision,
            "action": action,
            "note": "Overwrite",
        },
        format="json",
    )
    assert response.status_code == 409
    item.refresh_from_db()
    assert item.status == "resolved" and item.revision == 1 and item.responses == []


def test_private_revocation_covers_dispute_collection_detail_and_reply(phase6_lease):
    owner, tenant, lease = phase6_lease
    item = dispute(lease, tenant)
    PrivateAccessRevocation.objects.create(
        lease=lease, user=tenant, reason="Privacy restriction"
    )
    client = client_for(tenant)
    response = client.get(reverse("rental-disputes"))
    assert response.status_code == 200
    assert str(item.id) not in response.content.decode()
    assert (
        client.get(reverse("rental-dispute-detail", args=[item.id])).status_code == 404
    )
    assert (
        client.post(
            reverse("rental-dispute-respond", args=[item.id]),
            {
                "request_key": str(uuid.uuid4()),
                "expected_revision": 1,
                "action": "reply",
                "note": "Hidden",
            },
            format="json",
        ).status_code
        == 404
    )


def test_create_dispute_and_receipt_rollback_together(phase6_lease):
    owner, tenant, lease = phase6_lease
    invoice = RentInvoice.objects.create(
        lease=lease, reference="AUDIT-CASE", due_date=lease.start_date, amount_minor=100
    )
    payload = {
        "lease_id": str(lease.id),
        "subject_kind": "invoice",
        "subject_id": str(invoice.id),
        "request_key": str(uuid.uuid4()),
        "reason": "Review charge",
    }
    client = client_for(tenant)
    with patch(
        "core_apps.features.rental_phase6_views_parts.disputes.remember_mutation",
        side_effect=RuntimeError("Simulated crash"),
    ):
        assert (
            client.post(reverse("rental-disputes"), payload, format="json").status_code
            == 500
        )
    assert not RentalDispute.objects.filter(lease=lease).exists()
    first = client.post(reverse("rental-disputes"), payload, format="json")
    second = client.post(reverse("rental-disputes"), payload, format="json")
    assert first.status_code == second.status_code == 201
    assert first.data == second.data
    assert RentalDispute.objects.filter(lease=lease).count() == 1
