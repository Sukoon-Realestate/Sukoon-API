import uuid
from datetime import date, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import (
    Lease,
    MaintenanceRequest,
    RentalChange,
    RentInvoice,
)
from core_apps.features.providers import sign_fake_webhook
from core_apps.features.tasks import process_rental_changes
from core_apps.properties.models import City, Governorate, Property, PropertyType
from core_apps.users.models import User


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def phase5_lease(db):
    owner = User.objects.create_user(
        email="p5-owner@example.com", password="pass", is_verified=True
    )
    tenant = User.objects.create_user(
        email="p5-tenant@example.com", password="pass", is_verified=True
    )
    governorate = Governorate.objects.create(name="P5 Cairo")
    city = City.objects.create(name="P5 City", governorate=governorate)
    property_type = PropertyType.objects.create(
        name="P5 Apartment", slug="p5-apartment"
    )
    property_obj = Property.objects.create(
        owner=owner,
        title="P5 Home",
        price=10000,
        property_type=property_type,
        governorate=governorate,
        city=city,
        district="District",
        status=Property.Status.VERIFIED,
        is_verified=True,
        is_ownership_verified=True,
    )
    terms = {
        "starts_on": "2026-01-01",
        "ends_on_exclusive": "2027-01-01",
        "handover_on": "2026-01-01",
        "monthly_rent": {"amount_minor": 1_000_000, "currency": "EGP", "exponent": 2},
        "template_id": "eg-v1",
        "template_version": "1",
        "renewal_commission_rate_bps": 0,
    }
    lease = Lease.objects.create(
        property=property_obj,
        owner=owner,
        tenant=tenant,
        template_id="eg-v1",
        template_version="1",
        start_date=date(2026, 1, 1),
        end_date=date(2027, 1, 1),
        rent_amount_minor=1_000_000,
        status=Lease.Status.ACTIVE,
        occupancy_status=Lease.OccupancyStatus.OCCUPIED,
        legacy_read_only=False,
        offer_id=str(uuid.uuid4()),
        terms=terms,
    )
    return owner, tenant, lease


def action(client, request_id, name, revision, **extra):
    return client.post(
        f"/api/v1/features/v1/maintenance-requests/{request_id}/actions/",
        {
            "action": name,
            "expected_revision": revision,
            "request_key": str(uuid.uuid4()),
            **extra,
        },
        format="json",
    )


@pytest.mark.django_db
def test_complete_maintenance_vocabulary_and_exact_cost_approval(phase5_lease):
    owner, tenant, lease = phase5_lease
    created = client_for(tenant).post(
        f"/api/v1/features/v1/leases/{lease.id}/maintenance-requests/",
        {
            "title": "Water leak",
            "description": "Kitchen pipe is leaking",
            "category": "plumbing",
            "priority": "urgent",
            "access_times": ["morning"],
            "evidence_ids": [],
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
        },
        format="json",
    )
    assert created.status_code == 201
    item_id = created.data["resource"]["id"]
    owner_client = client_for(owner)
    tenant_client = client_for(tenant)
    assert action(owner_client, item_id, "start_work", 1).status_code == 409
    assert action(owner_client, item_id, "acknowledge", 1).status_code == 200
    assert (
        action(tenant_client, item_id, "reply", 2, note="Thank you").status_code == 200
    )
    proposed_cost = action(
        owner_client,
        item_id,
        "propose_cost",
        3,
        cost={"amount_minor": 50_000, "currency": "EGP", "exponent": 2},
        cost_payer="tenant",
    )
    assert proposed_cost.status_code == 200
    assert (
        action(owner_client, item_id, "approve_cost", 4, cost_version=1).status_code
        == 403
    )
    assert (
        action(tenant_client, item_id, "approve_cost", 4, cost_version=99).status_code
        == 409
    )
    assert (
        action(tenant_client, item_id, "approve_cost", 4, cost_version=1).status_code
        == 200
    )
    appointment = (timezone.now() + timedelta(days=1)).isoformat()
    assert (
        action(
            owner_client, item_id, "propose_appointment", 5, appointment_at=appointment
        ).status_code
        == 200
    )
    assert action(tenant_client, item_id, "accept_appointment", 6).status_code == 200
    assert action(owner_client, item_id, "start_work", 7).status_code == 200
    assert action(owner_client, item_id, "report_resolved", 8).status_code == 200
    assert action(tenant_client, item_id, "confirm_resolved", 9).status_code == 200
    assert action(tenant_client, item_id, "reopen", 10).status_code == 200
    assert action(tenant_client, item_id, "cancel", 11).status_code == 200
    item = MaintenanceRequest.objects.get(id=item_id)
    assert item.status == MaintenanceRequest.Status.CANCELLED
    assert item.events.count() == 12


@pytest.mark.django_db
def test_extension_preserves_due_at_and_external_claim_is_not_capture(phase5_lease):
    owner, tenant, lease = phase5_lease
    due_at = timezone.now() + timedelta(days=2)
    invoice = RentInvoice.objects.create(
        lease=lease,
        reference="P5-INVOICE",
        due_date=due_at.date(),
        due_at=due_at,
        amount_minor=1_000_000,
        charges_minor=1_000_000,
        status=RentInvoice.Status.DUE,
    )
    created = client_for(tenant).post(
        f"/api/v1/features/v1/leases/{lease.id}/payment-extension-requests/",
        {
            "invoice_id": str(invoice.id),
            "reason": "Salary timing",
            "requested_date": str(due_at.date() + timedelta(days=5)),
            "lease_revision": lease.revision,
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
        },
        format="json",
    )
    change = created.data["resource"]
    accepted = client_for(owner).post(
        f"/api/v1/features/v1/payment-extension-requests/{change['id']}/respond/",
        {
            "action": "accept",
            "expected_revision": change["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert accepted.data["resource"]["status"] == "applied"
    invoice.refresh_from_db()
    assert invoice.due_at == due_at
    assert invoice.deferred_until > invoice.due_at

    claim = client_for(tenant).post(
        f"/api/v1/features/v1/rent-invoices/{invoice.id}/external-payment-claims/",
        {
            "reason": "Paid by transfer",
            "method": "bank_transfer",
            "amount": {"amount_minor": 1_000_000},
            "evidence_ids": [],
            "lease_revision": lease.revision,
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
        },
        format="json",
    )
    claim_id = claim.data["resource"]["id"]
    assert claim.data["resource"]["status"] == "review_required"
    assert (
        client_for(tenant)
        .post(
            f"/api/v1/features/v1/external-payment-claims/{claim_id}/respond/",
            {
                "action": "accept",
                "expected_revision": 1,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        .status_code
        == 403
    )
    operator = User.objects.create_user(
        email="p5-finance@example.com", password="pass", is_verified=True
    )
    StaffProfile.objects.create(
        user=operator, role_name=StaffProfile.RoleName.FINANCIAL_APPROVER
    )
    assert (
        client_for(operator)
        .post(
            f"/api/v1/features/v1/external-payment-claims/{claim_id}/respond/",
            {
                "action": "accept",
                "expected_revision": 1,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        .status_code
        == 200
    )
    invoice.refresh_from_db()
    assert invoice.status == RentInvoice.Status.DUE
    assert invoice.applied_minor == 0


@pytest.mark.django_db
def test_amendment_invalid_signature_is_rejected_and_signed_change_applies(
    phase5_lease,
):
    owner, tenant, lease = phase5_lease
    terms = {
        **lease.terms,
        "monthly_rent": {"amount_minor": 1_100_000, "currency": "EGP", "exponent": 2},
    }
    created = client_for(owner).post(
        f"/api/v1/features/v1/leases/{lease.id}/amendments/",
        {
            "reason": "Agreed rent change",
            "effective_on": str(timezone.localdate()),
            "terms": terms,
            "evidence_ids": [],
            "lease_revision": lease.revision,
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
        },
        format="json",
    )
    item = created.data["resource"]
    accepted = client_for(tenant).post(
        f"/api/v1/features/v1/amendments/{item['id']}/respond/",
        {
            "action": "accept",
            "expected_revision": item["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    item = accepted.data["resource"]
    submitted = client_for(owner).post(
        f"/api/v1/features/v1/amendments/{item['id']}/submit-for-signature/",
        {
            "action": "submit_for_signature",
            "expected_revision": item["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    item = submitted.data["resource"]
    sessions = []
    for user in (owner, tenant):
        response = client_for(user).post(
            f"/api/v1/features/v1/amendments/{item['id']}/signing-session/",
            {
                "document_id": item["document_id"],
                "document_hash": item["document_hash"],
                "expected_revision": item["revision"],
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        sessions.append(response.data["resource"])
    bad = {
        "type": "change-signature.completed",
        "provider_session_id": sessions[0]["session_id"],
    }
    assert (
        APIClient()
        .post(
            "/api/v1/features/v1/provider-webhooks/rental/",
            bad,
            format="json",
            HTTP_X_RENTAL_SIGNATURE=sign_fake_webhook(bad),
        )
        .status_code
        == 404
    )
    from core_apps.features.models import ChangeSigningSession

    for session_data in sessions:
        session = ChangeSigningSession.objects.get(id=session_data["session_id"])
        payload = {
            "type": "change-signature.completed",
            "provider_session_id": session.provider_session_id,
        }
        assert (
            APIClient()
            .post(
                "/api/v1/features/v1/provider-webhooks/rental/",
                payload,
                format="json",
                HTTP_X_RENTAL_SIGNATURE=sign_fake_webhook(payload),
            )
            .status_code
            == 200
        )
    assert process_rental_changes()["applied"] == 1
    lease.refresh_from_db()
    assert lease.rent_amount_minor == 1_100_000
    change = RentalChange.objects.get(id=item["id"])
    assert change.previous_terms["monthly_rent"]["amount_minor"] == 1_000_000
