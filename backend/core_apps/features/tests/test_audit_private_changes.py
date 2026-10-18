"""Private change endpoints must honor current access, not cached authority."""

import uuid
import pytest
from django.urls import reverse
from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import (
    PrivateAccessRevocation,
    RentalChange,
    MaintenanceRequest,
)
from core_apps.features.tests.test_rental_phase6 import phase6_lease, client_for

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "kind,route,collection",
    [
        ("payment_extension", "payment-extension", "payment-extension-requests"),
        ("amendment", "amendment", "amendments"),
        ("renewal", "renewal", "renewals"),
        ("termination", "termination", "termination-requests"),
        ("external_payment", "external-claim", "external-payment-claims"),
    ],
)
def test_revoked_party_cannot_read_or_respond_to_private_change(
    phase6_lease, kind, route, collection
):
    owner, tenant, lease = phase6_lease
    item = RentalChange.objects.create(lease=lease, requester=owner, kind=kind)
    PrivateAccessRevocation.objects.create(
        lease=lease, user=tenant, reason="Explicit restriction"
    )
    client = client_for(tenant)
    assert (
        client.get(f"/api/v1/features/v1/leases/{lease.id}/{collection}/").status_code
        == 404
    )
    assert client.get(reverse(route + "-detail", args=[item.id])).status_code == 404
    result = client.post(
        reverse(route + "-respond", args=[item.id]),
        {"request_key": str(uuid.uuid4()), "expected_revision": 1, "action": "reject"},
        format="json",
    )
    assert result.status_code == 404
    item.refresh_from_db()
    assert item.status == "proposed" and item.revision == 1


def test_external_claim_read_uses_current_staff_authority(phase6_lease, user):
    owner, _, lease = phase6_lease
    item = RentalChange.objects.create(
        lease=lease, requester=owner, kind="external_payment"
    )
    profile = StaffProfile.objects.create(
        user=user, role_name="financial_approver", is_active=True
    )
    assert (
        user.staff_profile.is_active
    )  # Populate the same cache an earlier permission check could fill.
    client = client_for(user)
    endpoint = reverse("external-claim-detail", args=[item.id])
    assert client.get(endpoint).status_code == 200
    StaffProfile.objects.filter(pk=profile.pk).update(is_active=False)
    assert client.get(endpoint).status_code == 404


def test_revoked_party_cannot_read_or_mutate_maintenance(phase6_lease):
    _, tenant, lease = phase6_lease
    item = MaintenanceRequest.objects.create(
        lease=lease,
        reporter=tenant,
        title="Private repair",
        description="Restricted details",
        category="plumbing",
        priority="normal",
    )
    client = client_for(tenant)
    PrivateAccessRevocation.objects.create(
        lease=lease, user=tenant, reason="Explicit restriction"
    )
    assert (
        client.get(
            f"/api/v1/features/v1/leases/{lease.id}/maintenance-requests/"
        ).status_code
        == 404
    )
    assert (
        client.get(f"/api/v1/features/v1/maintenance-requests/{item.id}/").status_code
        == 404
    )
    response = client.post(
        f"/api/v1/features/v1/maintenance-requests/{item.id}/actions/",
        {
            "action": "reply",
            "note": "Must not persist",
            "expected_revision": 1,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert response.status_code == 404
    assert not item.events.exists()
