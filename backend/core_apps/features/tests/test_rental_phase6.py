import uuid
from datetime import date

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import (
    BillingPeriod,
    InvoicePaymentAllocation,
    Lease,
    LedgerTransaction,
    OwnerPayable,
    PaymentAttempt,
    PaymentQuote,
    RentalDispute,
    RentalHandover,
    RefundRequest,
    RentInvoice,
)
from core_apps.features.providers import sign_fake_webhook
from core_apps.features.tasks import process_rental_closure
from core_apps.properties.models import City, Governorate, Property, PropertyType
from core_apps.users.models import User


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def phase6_lease(db):
    owner = User.objects.create_user(
        email="p6-owner@example.com", password="pass", is_verified=True
    )
    tenant = User.objects.create_user(
        email="p6-tenant@example.com", password="pass", is_verified=True
    )
    governorate = Governorate.objects.create(name="P6 Cairo")
    city = City.objects.create(name="P6 City", governorate=governorate)
    property_type = PropertyType.objects.create(
        name="P6 Apartment", slug="p6-apartment"
    )
    property_obj = Property.objects.create(
        owner=owner,
        title="P6 Home",
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
        start_date=date(2025, 1, 1),
        end_date=date(2026, 1, 1),
        rent_amount_minor=1_000_000,
        status=Lease.Status.ENDED,
        occupancy_status=Lease.OccupancyStatus.RETURNED,
        legacy_read_only=False,
        offer_id=str(uuid.uuid4()),
        terms={"policy_version": "rental-policy-v1"},
    )
    RentalHandover.objects.create(
        lease=lease,
        kind=RentalHandover.Kind.MOVE_IN,
        possession_on=lease.start_date,
        status=RentalHandover.Status.ACCEPTED,
        approvals=[str(owner.id), str(tenant.id)],
    )
    RentalHandover.objects.create(
        lease=lease,
        kind=RentalHandover.Kind.MOVE_OUT,
        possession_on=lease.end_date,
        status=RentalHandover.Status.ACCEPTED,
        approvals=[str(owner.id), str(tenant.id)],
    )
    return owner, tenant, lease


def captured_payment(lease, tenant, reference="P6-RENT"):
    period = BillingPeriod.objects.create(
        lease=lease,
        sequence=1,
        start=lease.start_date,
        end_exclusive=lease.end_date,
        issue_at=timezone.now(),
        due_at=timezone.now(),
        amount_minor=1_000_000,
        status=BillingPeriod.Status.PAID,
    )
    invoice = RentInvoice.objects.create(
        lease=lease,
        billing_period=period,
        reference=reference,
        due_date=lease.start_date,
        due_at=timezone.now(),
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
        fingerprint="f" * 64,
        expires_at=timezone.now(),
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
    InvoicePaymentAllocation.objects.create(
        invoice=invoice, payment_attempt=attempt, amount_minor=1_000_000
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
        payout_status="succeeded",
        blocking_reasons=[],
    )
    return invoice, attempt, payable


def accepted_zero_settlement(owner, tenant, lease):
    initial = (
        client_for(owner)
        .get(f"/api/v1/features/v1/leases/{lease.id}/final-settlement/")
        .data
    )
    proposed = client_for(owner).post(
        f"/api/v1/features/v1/leases/{lease.id}/final-settlement/propose/",
        {
            "lines": [],
            "expected_revision": initial["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    item = proposed.data["resource"]
    accepted = client_for(tenant).post(
        f"/api/v1/features/v1/leases/{lease.id}/final-settlement/respond/",
        {
            "action": "accept",
            "expected_revision": item["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    return accepted.data["resource"]


@pytest.mark.django_db
def test_settlement_dispute_items_closure_and_late_chargeback_reopens(phase6_lease):
    owner, tenant, lease = phase6_lease
    invoice, attempt, _ = captured_payment(lease, tenant)
    initial = (
        client_for(owner)
        .get(f"/api/v1/features/v1/leases/{lease.id}/final-settlement/")
        .data
    )
    line_id = str(uuid.uuid4())
    proposed = client_for(owner).post(
        f"/api/v1/features/v1/leases/{lease.id}/final-settlement/propose/",
        {
            "lines": [
                {
                    "id": line_id,
                    "type": "damage",
                    "label": "Wall",
                    "amount": {"amount_minor": 0},
                    "evidence_ids": [],
                }
            ],
            "expected_revision": initial["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    item = proposed.data["resource"]
    bad = client_for(tenant).post(
        f"/api/v1/features/v1/leases/{lease.id}/final-settlement/respond/",
        {
            "action": "dispute",
            "item_ids": [str(uuid.uuid4())],
            "expected_revision": item["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert bad.status_code == 400
    accepted = client_for(tenant).post(
        f"/api/v1/features/v1/leases/{lease.id}/final-settlement/respond/",
        {
            "action": "accept",
            "expected_revision": item["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert accepted.data["resource"]["status"] == "accepted"
    lease.refresh_from_db()
    assert lease.financial_closure_status == Lease.FinancialClosureStatus.CLOSED

    chargeback = {
        "event_id": "p6-chargeback",
        "type": "payment.chargeback",
        "sequence": 3,
        "payment_attempt_id": str(attempt.id),
        "amount_minor": 1_000_000,
        "currency": "EGP",
    }
    response = APIClient().post(
        "/api/v1/features/v1/provider-webhooks/payments/",
        chargeback,
        format="json",
        HTTP_X_RENTAL_SIGNATURE=sign_fake_webhook(chargeback),
    )
    assert response.status_code == 200
    lease.refresh_from_db()
    assert lease.financial_closure_status == Lease.FinancialClosureStatus.OPEN
    assert lease.occupancy_status == Lease.OccupancyStatus.RETURNED
    invoice.refresh_from_db()
    assert invoice.status == RentInvoice.Status.DUE


@pytest.mark.django_db
def test_refund_balance_duplicate_worker_and_proportional_commission(phase6_lease):
    owner, tenant, lease = phase6_lease
    _, attempt, payable = captured_payment(lease, tenant, "P6-REFUND")
    body = {
        "payment_attempt_id": str(attempt.id),
        "amount": {"amount_minor": 500_000},
        "reason": "Agreed partial refund",
        "request_key": str(uuid.uuid4()),
        "expected_revision": 0,
    }
    created = client_for(tenant).post(
        "/api/v1/features/v1/refund-requests/", body, format="json"
    )
    assert created.status_code == 201
    assert (
        client_for(tenant)
        .post(
            "/api/v1/features/v1/refund-requests/",
            {
                **body,
                "request_key": str(uuid.uuid4()),
                "amount": {"amount_minor": 500_001},
            },
            format="json",
        )
        .status_code
        == 409
    )
    operator = User.objects.create_user(
        email="p6-refund@example.com", password="pass", is_verified=True
    )
    StaffProfile.objects.create(
        user=operator, role_name=StaffProfile.RoleName.REFUND_OPERATOR
    )
    refund_id = created.data["resource"]["id"]
    approved = client_for(operator).post(
        f"/api/v1/features/v1/refund-requests/{refund_id}/respond/",
        {"action": "approve", "expected_revision": 1, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert approved.status_code == 200
    assert process_rental_closure()["refunds"] == 1
    assert process_rental_closure()["refunds"] == 0
    refund = RefundRequest.objects.get(id=refund_id)
    payable.refresh_from_db()
    assert refund.status == RefundRequest.Status.SUCCEEDED
    assert payable.commission_minor == 50_000
    tx = LedgerTransaction.objects.get(reference=f"refund:{refund.id}")
    assert sum(x.amount_minor for x in tx.entries.filter(direction="debit")) == 500_000
    assert sum(x.amount_minor for x in tx.entries.filter(direction="credit")) == 500_000


@pytest.mark.django_db
def test_legacy_reconciliation_preserves_identifiers_and_financial_facts(phase6_lease):
    _, _, lease = phase6_lease
    lease.document_id = None
    lease.document_hash = ""
    lease.legacy_read_only = False
    lease.save()
    original_id = lease.id
    original_rent = lease.rent_amount_minor

    call_command("reconcile_legacy_rentals", "--apply")

    lease.refresh_from_db()
    assert lease.id == original_id
    assert lease.rent_amount_minor == original_rent
    assert lease.legacy_read_only is True


@pytest.mark.django_db
def test_dispute_documents_reviews_and_private_authorization(phase6_lease):
    owner, tenant, lease = phase6_lease
    invoice, _, _ = captured_payment(lease, tenant, "P6-DOCS")
    dispute = client_for(tenant).post(
        "/api/v1/features/v1/disputes/",
        {
            "lease_id": str(lease.id),
            "subject_kind": "invoice",
            "subject_id": str(invoice.id),
            "reason": "Amount questioned",
            "evidence_ids": [],
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
        },
        format="json",
    )
    dispute_id = dispute.data["resource"]["id"]
    reply = client_for(owner).post(
        f"/api/v1/features/v1/disputes/{dispute_id}/respond/",
        {
            "action": "reply",
            "note": "Reviewing",
            "expected_revision": 1,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert len(reply.data["resource"]["responses"]) == 1
    resolver = User.objects.create_user(
        email="p6-resolver@example.com", password="pass", is_verified=True
    )
    StaffProfile.objects.create(
        user=resolver, role_name=StaffProfile.RoleName.DISPUTE_RESOLVER
    )
    resolved = client_for(resolver).post(
        f"/api/v1/features/v1/disputes/{dispute_id}/respond/",
        {
            "action": "resolve",
            "note": "Resolved from records",
            "expected_revision": 2,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert resolved.data["resource"]["status"] == RentalDispute.Status.RESOLVED

    statement = client_for(tenant).post(
        "/api/v1/features/v1/rental-statements/",
        {
            "lease_id": str(lease.id),
            "starts_on": "2025-01-01",
            "ends_on_exclusive": "2026-01-01",
            "request_key": str(uuid.uuid4()),
            "expected_revision": lease.revision,
        },
        format="json",
    )
    document_id = statement.data["resource"]["id"]
    assert process_rental_closure()["documents"] == 1
    link = client_for(owner).get(
        f"/api/v1/features/v1/rental-documents/{document_id}/download/"
    )
    assert link.status_code == 200 and "token=" in link.data["url"]
    stranger = User.objects.create_user(
        email="p6-stranger@example.com", password="pass"
    )
    assert (
        client_for(stranger)
        .get(f"/api/v1/features/v1/rental-documents/{document_id}/download/")
        .status_code
        == 404
    )

    review_body = {
        "rating": 5,
        "comment": "Good tenancy",
        "expected_revision": 0,
        "request_key": str(uuid.uuid4()),
    }
    assert (
        client_for(tenant)
        .post(
            f"/api/v1/features/v1/leases/{lease.id}/reviews/",
            review_body,
            format="json",
        )
        .status_code
        == 201
    )
    assert (
        client_for(tenant)
        .post(
            f"/api/v1/features/v1/leases/{lease.id}/reviews/",
            {**review_body, "request_key": str(uuid.uuid4())},
            format="json",
        )
        .status_code
        == 409
    )
