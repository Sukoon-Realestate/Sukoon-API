import hashlib
import uuid
from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import (
    BillingPeriod,
    Lease,
    LedgerTransaction,
    OwnerPayable,
    OwnerPaymentProfile,
    PaymentAttempt,
    PaymentQuote,
    RentalEvidence,
    RentalHandover,
    RentalPayout,
    RentInvoice,
)
from core_apps.features.tasks import reconcile_approved_payouts, scan_rental_evidence
from core_apps.properties.models import City, Governorate, Property, PropertyType
from core_apps.users.models import User


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def phase4_lease(db):
    owner = User.objects.create_user(
        email="p4-owner@example.com", password="pass", is_verified=True
    )
    tenant = User.objects.create_user(
        email="p4-tenant@example.com", password="pass", is_verified=True
    )
    governorate = Governorate.objects.create(name="P4 Cairo")
    city = City.objects.create(name="P4 City", governorate=governorate)
    property_type = PropertyType.objects.create(
        name="P4 Apartment", slug="p4-apartment"
    )
    property_obj = Property.objects.create(
        owner=owner,
        title="P4 Home",
        price=10000,
        property_type=property_type,
        governorate=governorate,
        city=city,
        district="District",
        status=Property.Status.VERIFIED,
        is_verified=True,
        is_ownership_verified=True,
    )
    lease = Lease.objects.create(
        property=property_obj,
        owner=owner,
        tenant=tenant,
        template_id="eg-v1",
        template_version="1",
        start_date=date(2026, 10, 10),
        end_date=date(2027, 10, 10),
        rent_amount_minor=1_000_000,
        status=Lease.Status.ACTIVE,
        legacy_read_only=False,
        offer_id=str(uuid.uuid4()),
        terms={
            "deposit": {"amount_minor": 200_000, "currency": "EGP", "exponent": 2},
            "deposit_holder": "platform",
        },
    )
    return owner, tenant, lease


def upload_evidence(user, lease, content=b"\x89PNG\r\n\x1a\nimage-content"):
    digest = hashlib.sha256(content).hexdigest()
    response = client_for(user).post(
        "/api/v1/features/v1/rental-attachments/",
        {
            "lease_id": str(lease.id),
            "request_key": str(uuid.uuid4()),
            "mime_type": "image/png",
            "sha256": digest,
            "file": SimpleUploadedFile(
                "condition.png", content, content_type="image/png"
            ),
        },
        format="multipart",
    )
    return response


@pytest.mark.django_db
def test_private_evidence_validation_scan_recovery_and_download(phase4_lease):
    owner, tenant, lease = phase4_lease
    response = upload_evidence(tenant, lease)
    assert response.status_code == 201
    evidence = RentalEvidence.objects.get(id=response.data["resource"]["id"])
    assert response.data["resource"]["status"] == "pending"
    assert scan_rental_evidence()["safe"] == 1
    detail = client_for(owner).get(
        f"/api/v1/features/v1/rental-attachments/{evidence.id}/"
    )
    assert detail.data["status"] == "ready"
    link = client_for(tenant).get(
        f"/api/v1/features/v1/rental-attachments/{evidence.id}/download/"
    )
    assert link.status_code == 200
    assert "token=" in link.data["url"]

    wrong = upload_evidence(tenant, lease, b"not-a-png")
    assert wrong.status_code == 400
    stranger = User.objects.create_user(
        email="p4-stranger@example.com", password="pass"
    )
    assert (
        client_for(stranger)
        .get(f"/api/v1/features/v1/rental-attachments/{evidence.id}/")
        .status_code
        == 404
    )


@pytest.mark.django_db
def test_handover_revision_invalidation_acceptance_and_deposit_separation(phase4_lease):
    owner, tenant, lease = phase4_lease
    evidence_response = upload_evidence(tenant, lease)
    scan_rental_evidence()
    evidence_id = evidence_response.data["resource"]["id"]
    body = {
        "kind": "move_in",
        "possession_on": "2026-10-10",
        "condition": {"summary": "good"},
        "keys": {"count": 2},
        "meters": {"electricity": "10"},
        "inventory": [],
        "evidence_ids": [evidence_id],
        "request_key": str(uuid.uuid4()),
        "expected_revision": 0,
    }
    created = client_for(owner).post(
        f"/api/v1/features/v1/leases/{lease.id}/handovers/", body, format="json"
    )
    assert created.status_code == 201
    handover_id = created.data["resource"]["id"]
    accepted_owner = client_for(owner).post(
        f"/api/v1/features/v1/handovers/{handover_id}/respond/",
        {"action": "accept", "expected_revision": 1, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert accepted_owner.status_code == 200
    updated = client_for(owner).patch(
        f"/api/v1/features/v1/handovers/{handover_id}/",
        {
            **body,
            "condition": {"summary": "excellent"},
            "expected_revision": 2,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert updated.data["resource"]["accepted_by"] == []
    assert (
        client_for(owner)
        .post(
            f"/api/v1/features/v1/handovers/{handover_id}/respond/",
            {
                "action": "accept",
                "expected_revision": 3,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        .status_code
        == 200
    )
    final = client_for(tenant).post(
        f"/api/v1/features/v1/handovers/{handover_id}/respond/",
        {"action": "accept", "expected_revision": 4, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert final.data["resource"]["status"] == "accepted"
    lease.refresh_from_db()
    assert lease.occupancy_status == Lease.OccupancyStatus.OCCUPIED

    deposit = client_for(tenant).get(f"/api/v1/features/v1/leases/{lease.id}/deposit/")
    assert deposit.data["agreed"]["amount_minor"] == 200_000
    assert deposit.data["collected"]["amount_minor"] == 0
    assert (
        RentInvoice.objects.get(id=deposit.data["invoice_id"]).invoice_type
        == RentInvoice.InvoiceType.DEPOSIT
    )


@pytest.mark.django_db
def test_only_operations_can_execute_each_eligible_payable_once(phase4_lease):
    owner, tenant, lease = phase4_lease
    OwnerPaymentProfile.objects.create(
        owner=owner,
        status=OwnerPaymentProfile.Status.READY,
        payout_ready=True,
        accepted_policy_versions=["rental-policy-v1"],
        masked_beneficiary={"account_last4": "4242"},
    )
    RentalHandover.objects.create(
        lease=lease,
        kind=RentalHandover.Kind.MOVE_IN,
        possession_on=lease.start_date,
        status=RentalHandover.Status.ACCEPTED,
        approvals=[str(owner.id), str(tenant.id)],
    )
    period = BillingPeriod.objects.create(
        lease=lease,
        sequence=1,
        start=lease.start_date,
        end_exclusive=date(2026, 11, 10),
        issue_at="2026-10-09T00:00:00Z",
        due_at="2026-10-10T00:00:00Z",
        amount_minor=1_000_000,
    )
    invoice = RentInvoice.objects.create(
        lease=lease,
        billing_period=period,
        reference="P4-RENT",
        due_date=lease.start_date,
        amount_minor=1_000_000,
        charges_minor=1_000_000,
        applied_minor=1_000_000,
        status=RentInvoice.Status.PAID,
    )
    quote = PaymentQuote.objects.create(
        invoice=invoice,
        request_key=uuid.uuid4(),
        invoice_revision=1,
        payer_amount_minor=1_000_000,
        policy_version="rental-policy-v1",
        fingerprint="a" * 64,
        expires_at="2026-10-10T00:00:00Z",
    )
    attempt = PaymentAttempt.objects.create(
        invoice=invoice,
        payer=tenant,
        quote=quote,
        request_key=uuid.uuid4(),
        invoice_revision=1,
        policy_version="rental-policy-v1",
        quote_fingerprint=quote.fingerprint,
        payment_status=PaymentAttempt.Status.CAPTURED,
        amount_minor=1_000_000,
        settlement_status="settled",
    )
    payable = OwnerPayable.objects.create(
        lease=lease,
        invoice=invoice,
        payment_attempt=attempt,
        billing_period=period,
        gross_minor=1_000_000,
        commission_minor=100_000,
        net_minor=900_000,
        settlement_status="settled",
        payout_status="ready",
        blocking_reasons=[],
    )
    assert (
        client_for(owner)
        .post(
            "/api/v1/features/v1/operations/payouts/execute/",
            {"payable_ids": [str(payable.id)], "request_key": str(uuid.uuid4())},
            format="json",
        )
        .status_code
        == 403
    )

    operator = User.objects.create_user(
        email="p4-operator@example.com", password="pass", is_verified=True
    )
    StaffProfile.objects.create(
        user=operator, role_name=StaffProfile.RoleName.PAYOUT_OPERATOR
    )
    created = client_for(operator).post(
        "/api/v1/features/v1/operations/payouts/execute/",
        {"payable_ids": [str(payable.id)], "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert created.status_code == 201
    second = client_for(operator).post(
        "/api/v1/features/v1/operations/payouts/execute/",
        {"payable_ids": [str(payable.id)], "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert second.status_code == 409
    assert reconcile_approved_payouts()["paid"] == 1
    assert reconcile_approved_payouts()["paid"] == 0
    payout = RentalPayout.objects.get(id=created.data["resource"]["id"])
    assert payout.status == RentalPayout.Status.PAID
    assert (
        LedgerTransaction.objects.get(reference=f"payout:{payout.id}").entries.count()
        == 2
    )
