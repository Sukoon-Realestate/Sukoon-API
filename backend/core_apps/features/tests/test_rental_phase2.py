import uuid
from datetime import timedelta

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.features.models import (
    DepositAgreement,
    IdempotencyRecord,
    Lease,
    OwnerOnboardingSession,
    OwnerPaymentProfile,
    OwnerPayable,
    PaymentAttempt,
    RentalInventoryDayLock,
    SigningSession,
    TenancyInvitation,
)
from core_apps.features.providers import sign_fake_webhook
from core_apps.features.providers import get_rental_provider
from core_apps.features.services.rental_phase2 import (
    RentalConflict,
    reserve_inventory_days,
)
from core_apps.features.tasks import expire_rental_sources_and_holds
from core_apps.properties.models import City, Governorate, Property, PropertyType
from core_apps.users.models import User


def authenticated(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def rental_participants(db):
    owner = User.objects.create_user(
        email="phase2-owner@example.com",
        password="pass",
        first_name="Phase",
        last_name="Owner",
        is_verified=True,
    )
    tenant = User.objects.create_user(
        email="phase2-tenant@example.com",
        password="pass",
        first_name="Phase",
        last_name="Tenant",
        is_verified=True,
    )
    stranger = User.objects.create_user(
        email="phase2-stranger@example.com",
        password="pass",
        first_name="Phase",
        last_name="Stranger",
        is_verified=True,
    )
    governorate = Governorate.objects.create(name="Phase Two Cairo")
    city = City.objects.create(name="Phase Two City", governorate=governorate)
    property_type = PropertyType.objects.create(
        name="Phase Two Apartment", slug="phase-two-apartment"
    )
    offer_id = str(uuid.uuid4())
    property_obj = Property.objects.create(
        owner=owner,
        title="Phase two home",
        price=10000,
        property_type=property_type,
        governorate=governorate,
        city=city,
        district="District",
        status=Property.Status.VERIFIED,
        is_verified=True,
        is_ownership_verified=True,
        rental_inventory={
            "schema_version": 1,
            "revision": 1,
            "mode": "whole",
            "rooms": [],
            "offers": [
                {
                    "id": offer_id,
                    "revision": 2,
                    "rental_scope": "entire_property",
                    "name": "Whole home",
                    "room_ids": [],
                    "availability": "available",
                    "archived": False,
                    "capacity": 2,
                    "terms": {"price": "10000", "price_period": "monthly"},
                }
            ],
        },
    )
    return owner, tenant, stranger, property_obj, offer_id


def complete_owner_onboarding(owner):
    client = authenticated(owner)
    profile_response = client.get("/api/v1/features/v1/owner-payment-profile/")
    profile = profile_response.data
    grant = client.get(
        f"/api/v1/features/v1/rental-capabilities/?subject_id={profile['id']}&action=onboard_beneficiary"
    )
    assert "owner_payouts" in grant.data["enabled_capabilities"]
    assert "onboard_beneficiary" in grant.data["allowed_actions"]
    request_key = str(uuid.uuid4())
    session_response = client.post(
        "/api/v1/features/v1/owner-payment-profile/onboarding-session/",
        {
            "expected_revision": profile["revision"],
            "request_key": request_key,
            "accepted_policy_versions": ["rental-policy-v1"],
        },
        format="json",
    )
    assert session_response.status_code == 201
    recovered = client.get(
        f"/api/v1/features/v1/rental-operations/{request_key}/?subject_id={profile['id']}"
    )
    assert recovered.status_code == 200
    assert (
        recovered.data["operation_receipt"]["subject_id"]
        == session_response.data["session_id"]
    )
    descriptor = session_response.data["mock_completion"]
    assert session_response.data["provider_mode"] == "mock"
    body = {
        "expected_revision": descriptor["expected_revision"],
        "request_key": str(uuid.uuid4()),
    }
    completed = client.post(descriptor["path"], body, format="json")
    assert completed.status_code == 200, completed.data
    assert client.post(descriptor["path"], body, format="json").data == completed.data
    return OwnerPaymentProfile.objects.get(owner=owner)


def agreement_terms(starts_on, ends_on):
    return {
        "starts_on": str(starts_on),
        "ends_on_exclusive": str(ends_on),
        "handover_on": str(starts_on),
        "monthly_rent": {
            "amount_minor": 1000000,
            "currency": "EGP",
            "exponent": 2,
        },
        "deposit": {"amount_minor": 1000000, "currency": "EGP", "exponent": 2},
        "deposit_holder": "platform",
        "included_services": [],
        "excluded_services": [],
        "termination_policy": {"notice_days": 30},
        "renewal_policy": {"automatic": False},
        "policy_version": "rental-policy-v1",
        "template_id": "eg-residential-v1",
        "template_version": "1",
        "timezone": "Africa/Cairo",
        "occupants": 1,
        "billing_anchor_day": starts_on.day,
        "commission_rate_bps": 1000,
        "commission_payer": "owner",
        "commission_basis": "first_period_base_rent",
        "processing_fee_payer": "platform",
        "renewal_commission_rate_bps": 0,
    }


@pytest.mark.django_db
def test_phase2_complete_interest_to_activation_flow(rental_participants):
    owner, tenant, _, property_obj, offer_id = rental_participants
    initial_owner_profile = (
        authenticated(owner)
        .get("/api/v1/features/v1/owner-payment-profile/")
        .json()["data"]
    )
    onboarding_grant = (
        authenticated(owner)
        .get(
            f"/api/v1/features/v1/rental-capabilities/?subject_id={initial_owner_profile['id']}&action=onboard_beneficiary"
        )
        .json()["data"]
    )
    profile = complete_owner_onboarding(owner)
    assert profile.status == OwnerPaymentProfile.Status.READY
    assert profile.masked_beneficiary == {"account_last4": "4242"}

    starts_on = timezone.localdate() + timedelta(days=10)
    ends_on = starts_on + timedelta(days=31)
    tenant_client = authenticated(tenant)
    owner_client = authenticated(owner)
    grants = {}
    signing_responses = []

    def grant(client, subject, action):
        response = client.get(
            f"/api/v1/features/v1/rental-capabilities/?subject_id={subject}&action={action}"
        )
        assert response.status_code == 200
        assert action in response.data["allowed_actions"], response.data
        assert response.data["blocking_reasons"] == []
        grants[str(subject) + ":" + action + ":" + response.data["account_id"]] = (
            response.json()["data"]
        )

    grant(tenant_client, property_obj.id, "create_rental_interest")

    interest_response = tenant_client.post(
        "/api/v1/features/v1/rental-interests/",
        {
            "property_id": str(property_obj.id),
            "offer_id": offer_id,
            "offer_revision": 2,
            "desired_start": str(starts_on),
            "months": 1,
            "occupants": 1,
            "message": "Interested",
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
        },
        format="json",
    )
    assert interest_response.status_code == 201
    interest = interest_response.data["resource"]
    grant(owner_client, interest["id"], "create_terms_proposal")

    proposal_response = owner_client.post(
        "/api/v1/features/v1/terms-proposals/",
        {
            "interest_id": interest["id"],
            "offer_id": offer_id,
            "terms": agreement_terms(starts_on, ends_on),
            "interest_revision": interest["revision"],
            "offer_revision": 2,
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
        },
        format="json",
    )
    assert proposal_response.status_code == 201
    proposal = proposal_response.data["resource"]
    grant(tenant_client, proposal["id"], "accept")

    accepted = tenant_client.post(
        f"/api/v1/features/v1/terms-proposals/{proposal['id']}/respond/",
        {
            "decision": "accept",
            "expected_revision": proposal["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert accepted.status_code == 200
    proposal = accepted.data["resource"]
    assert proposal["status"] == "accepted"
    grant(owner_client, interest["id"], "create_invitation")

    invitation_response = owner_client.post(
        "/api/v1/features/v1/tenancy-invitations/",
        {
            "interest_id": interest["id"],
            "interest_revision": 2,
            "property_id": str(property_obj.id),
            "offer_id": offer_id,
            "offer_revision": 2,
            "tenant_id": str(tenant.id),
            "terms_proposal_id": proposal["id"],
            "expected_revision": 0,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert invitation_response.status_code == 201
    invitation = invitation_response.data["resource"]

    invitation_accept = tenant_client.post(
        f"/api/v1/features/v1/tenancy-invitations/{invitation['id']}/respond/",
        {
            "decision": "accepted",
            "revision": invitation["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert invitation_accept.status_code == 200
    invitation = invitation_accept.data
    grant(owner_client, invitation["id"], "create_lease")

    lease_response = owner_client.post(
        "/api/v1/features/v1/leases/",
        {
            "invitation_id": invitation["id"],
            "invitation_revision": invitation["revision"],
            "property_id": str(property_obj.id),
            "offer_id": offer_id,
            "offer_revision": 2,
            "tenant_id": str(tenant.id),
            "terms": agreement_terms(starts_on, ends_on),
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
        },
        format="json",
    )
    assert lease_response.status_code == 201
    lease = lease_response.data["resource"]
    assert lease["legacy_read_only"] is False
    assert RentalInventoryDayLock.objects.filter(lease__id=lease["id"]).count() == 31
    grant(owner_client, lease["id"], "accept_review")
    details = owner_client.get(f"/api/v1/features/v1/leases/{lease['id']}/").data
    assert details["owner_id"] == str(owner.id)
    assert details["tenant_id"] == str(tenant.id)
    assert "accept_review" in details["allowed_actions"]

    owner_review = owner_client.post(
        f"/api/v1/features/v1/leases/{lease['id']}/review/",
        {
            "decision": "accept_review",
            "expected_revision": lease["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    tenant_review = tenant_client.post(
        f"/api/v1/features/v1/leases/{lease['id']}/review/",
        {
            "decision": "accept_review",
            "expected_revision": owner_review.data["resource"]["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    lease = tenant_review.data["resource"]
    grant(owner_client, lease["id"], "submit_for_signature")

    submitted = owner_client.post(
        f"/api/v1/features/v1/leases/{lease['id']}/submit-for-signature/",
        {
            "decision": "submit_for_signature",
            "expected_revision": lease["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert submitted.status_code == 200
    lease = submitted.data["resource"]
    assert lease["lease_status"] == "pending_signatures"

    sessions = []
    for client in (owner_client, tenant_client):
        grant(client, lease["id"], "sign")
        response = client.post(
            f"/api/v1/features/v1/leases/{lease['id']}/signing-session/",
            {
                "document_id": lease["document_id"],
                "document_hash": lease["document_hash"],
                "expected_revision": lease["revision"],
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        assert response.status_code == 201
        signing_responses.append(response.json()["data"])
        recovered = client.get(
            f"/api/v1/features/v1/rental-operations/{response.data['request_key']}/?subject_id={lease['id']}"
        )
        assert recovered.status_code == 200
        assert (
            recovered.data["operation_receipt"]["subject_id"]
            == response.data["session_id"]
        )
        sessions.append(SigningSession.objects.get(id=response.data["session_id"]))

    for session, client in zip(sessions, (owner_client, tenant_client)):
        payload = {
            "expected_revision": lease["revision"],
            "request_key": str(uuid.uuid4()),
        }
        completion_path = (
            f"/api/v1/features/v1/mock-provider/signing-sessions/{session.id}/complete/"
        )
        response = client.post(completion_path, payload, format="json")
        assert response.status_code == 200, response.data
        assert (
            client.post(completion_path, payload, format="json").data == response.data
        )

    signed = Lease.objects.get(id=lease["id"])
    assert signed.status == Lease.Status.SIGNED
    assert signed.activated_at is None
    assert (
        timedelta(hours=47, minutes=59)
        < signed.hold_expires_at - timezone.now()
        <= timedelta(hours=48)
    )
    assert set(
        RentalInventoryDayLock.objects.filter(lease=signed).values_list(
            "kind", flat=True
        )
    ) == {RentalInventoryDayLock.Kind.HOLD}
    assert signed.invoices.count() == 1
    invoice = signed.invoices.get()
    assert invoice.charges_minor == 2_000_000
    assert dict(invoice.lines.values_list("line_type", "amount_minor")) == {
        "base_rent": 1_000_000,
        "security_deposit": 1_000_000,
    }
    deposit = DepositAgreement.objects.get(lease=signed)
    assert deposit.invoice_id == invoice.pk
    assert deposit.collected_minor == 0
    assert deposit.due_minor == 1_000_000
    # A repeated signing callback cannot restart the hold or issue another bill.
    assert (
        tenant_client.post(completion_path, payload, format="json").status_code == 200
    )
    signed.refresh_from_db()
    assert signed.invoices.count() == 1
    initial_invoice = tenant_client.get(
        f"/api/v1/features/v1/rent-invoices/{invoice.id}/"
    ).json()["data"]
    assert initial_invoice["can_pay"] is True
    assert (
        initial_invoice["balance"]["amount_minor"]
        == initial_invoice["charges"]["amount_minor"]
        == 2_000_000
    )
    grant(tenant_client, invoice.id, "quote")
    quote = tenant_client.post(
        f"/api/v1/features/v1/rent-invoices/{invoice.id}/quote/",
        {
            "decision": "quote",
            "expected_revision": invoice.revision,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert quote.status_code == 201
    grant(tenant_client, invoice.id, "checkout")
    checkout_body = {
        "invoice_id": str(invoice.id),
        "quote_id": quote.data["resource"]["quote_id"],
        "expected_revision": invoice.revision,
        "request_key": str(uuid.uuid4()),
    }
    checkout = tenant_client.post(
        f"/api/v1/features/v1/rent-invoices/{invoice.id}/checkout/",
        checkout_body,
        format="json",
    )
    assert checkout.status_code == 201
    recovered = tenant_client.get(
        f"/api/v1/features/v1/rental-operations/{checkout_body['request_key']}/?subject_id={invoice.id}"
    )
    assert recovered.status_code == 200
    assert (
        recovered.data["operation_receipt"]["subject_id"]
        == checkout.data["resource"]["session_id"]
    )
    assert (
        tenant_client.post(
            f"/api/v1/features/v1/rent-invoices/{invoice.id}/checkout/",
            checkout_body,
            format="json",
        ).data
        == checkout.data
    )
    pending_lookup = tenant_client.get(
        f"/api/v1/features/v1/payment-attempts/?invoice_id={invoice.id}&request_key={checkout_body['request_key']}"
    )
    assert pending_lookup.status_code == 200
    recovered_session = pending_lookup.data["active_session"]
    assert recovered_session["session_id"] == checkout.data["resource"]["session_id"]
    assert (
        recovered_session["operation_receipt_id"]
        == checkout.data["operation_receipt"]["id"]
    )
    assert recovered_session["quote_id"] == checkout_body["quote_id"]
    attempt = PaymentAttempt.objects.get(
        id=checkout.data["resource"]["payment_attempt_id"]
    )
    capture = {
        "event": "captured",
        "expected_revision": attempt.revision,
        "request_key": str(uuid.uuid4()),
    }
    completion_path = (
        f"/api/v1/features/v1/mock-provider/payment-attempts/{attempt.id}/events/"
    )
    captured = tenant_client.post(completion_path, capture, format="json")
    assert captured.status_code == 200, captured.data
    assert (
        tenant_client.post(completion_path, capture, format="json").data
        == captured.data
    )
    settled = tenant_client.post(
        completion_path,
        {
            "event": "settled",
            "expected_revision": captured.data["resource"]["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert settled.status_code == 200, settled.data
    assert settled.data["resource"]["settlement_status"] == "settled"
    signed.refresh_from_db()
    invoice.refresh_from_db()
    deposit.refresh_from_db()
    assert signed.status == Lease.Status.ACTIVE and signed.activated_at
    assert signed.occupancy_status == Lease.OccupancyStatus.NOT_STARTED
    assert set(signed.inventory_day_locks.values_list("kind", flat=True)) == {
        RentalInventoryDayLock.Kind.OCCUPIED
    }
    assert invoice.status == "paid" and invoice.receipt_id
    assert deposit.collected_minor == 1_000_000 and deposit.due_minor == 0
    payable = OwnerPayable.objects.get(invoice=invoice)
    assert (payable.gross_minor, payable.commission_minor, payable.net_minor) == (
        1_000_000,
        100_000,
        900_000,
    )
    for client in (owner_client, tenant_client):
        read = client.get(f"/api/v1/features/v1/leases/{signed.id}/").data
        assert read["status"] == "active" and read["revision"] == signed.revision
        projection = client.get(f"/api/v1/features/v1/leases/{signed.id}/deposit/").data
        assert projection["invoice_id"] == str(invoice.id)
    assert signed.invoices.count() == 1
    for entry in attempt.ledger_transactions.all():
        assert sum(
            entry.entries.filter(direction="debit").values_list(
                "amount_minor", flat=True
            )
        ) == sum(
            entry.entries.filter(direction="credit").values_list(
                "amount_minor", flat=True
            )
        )

    grant(owner_client, signed.id, "create_rental_handover")
    moved = owner_client.post(
        f"/api/v1/features/v1/leases/{signed.id}/handovers/",
        {
            "kind": "move_in",
            "possession_on": str(starts_on),
            "condition": {"summary": "good"},
            "keys": {"count": 2},
            "meters": {},
            "inventory": [],
            "evidence_ids": [],
            "expected_revision": 0,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert moved.status_code == 201, moved.data
    handover = moved.data["resource"]
    for client in (owner_client, tenant_client):
        grant(client, handover["id"], "accept")
        moved = client.post(
            f"/api/v1/features/v1/handovers/{handover['id']}/respond/",
            {
                "decision": "accept",
                "expected_revision": handover["revision"],
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        assert moved.status_code == 200, moved.data
        handover = moved.data["resource"]
    signed.refresh_from_db()
    assert signed.occupancy_status == "occupied"
    payable.refresh_from_db()
    assert payable.payout_status == "ready"
    displayed_payables = owner_client.get(
        f"/api/v1/features/v1/owner-payables/?workspace=owner&lease_id={signed.id}"
    )
    assert displayed_payables.status_code == 200
    assert displayed_payables.data["results"][0]["invoice_id"] == str(invoice.id)
    grant(tenant_client, signed.id, "create_maintenance_request")
    maintenance = tenant_client.post(
        f"/api/v1/features/v1/leases/{signed.id}/maintenance-requests/",
        {
            "title": "Tap leak",
            "description": "Repair the tap",
            "category": "plumbing",
            "priority": "normal",
            "access_times": [],
            "evidence_ids": [],
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
        },
        format="json",
    )
    assert maintenance.status_code == 201, maintenance.data
    item = maintenance.data["resource"]
    for client, action in (
        (owner_client, "acknowledge"),
        (owner_client, "start_work"),
        (owner_client, "report_resolved"),
        (tenant_client, "confirm_resolved"),
    ):
        grant(client, item["id"], action)
        assert action in item["allowed_actions"]
        maintenance = client.post(
            f"/api/v1/features/v1/maintenance-requests/{item['id']}/actions/",
            {
                "action": action,
                "expected_revision": item["revision"],
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        assert maintenance.status_code == 200, maintenance.data
        item = maintenance.data["resource"]
    assert item["status"] == "resolved"

    import json, os
    from pathlib import Path

    if output := os.environ.get("SOKOUN_CONTRACT_ARTIFACT_DIR"):
        folder = Path(output)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "django-cycle-contract.json").write_text(
            json.dumps(
                {
                    "environment": "local-test-fake-provider",
                    "initial_invoice": initial_invoice,
                    "quote": quote.json()["data"],
                    "pending_lookup": pending_lookup.json()["data"],
                    "payment_attempt": captured.json()["data"]["resource"],
                    "grants": grants,
                    "signing_sessions": signing_responses,
                    "initial_owner_profile": initial_owner_profile,
                    "onboarding_grant": onboarding_grant,
                    "onboarding": IdempotencyRecord.objects.get(
                        user=owner, operation="rental.owner_onboarding.create"
                    ).response_data,
                    "active_lease": read,
                    "deposit": projection,
                    "checkout": checkout.json()["data"],
                    "owner_profile": owner_client.get(
                        "/api/v1/features/v1/owner-payment-profile/"
                    ).json()["data"],
                },
                indent=2,
            )
        )


@pytest.mark.django_db
def test_phase2_private_resources_and_stale_revisions(rental_participants):
    owner, tenant, stranger, property_obj, offer_id = rental_participants
    complete_owner_onboarding(owner)
    starts_on = timezone.localdate() + timedelta(days=10)
    response = authenticated(tenant).post(
        "/api/v1/features/v1/rental-interests/",
        {
            "property_id": str(property_obj.id),
            "offer_id": offer_id,
            "offer_revision": 2,
            "desired_start": str(starts_on),
            "months": 1,
            "occupants": 1,
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
        },
        format="json",
    )
    interest_id = response.data["resource"]["id"]
    assert (
        authenticated(stranger)
        .get(f"/api/v1/features/v1/rental-interests/{interest_id}/")
        .status_code
        == 404
    )
    stale = authenticated(owner).post(
        f"/api/v1/features/v1/rental-interests/{interest_id}/respond/",
        {
            "decision": "reject",
            "expected_revision": 99,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert stale.status_code == 409


@pytest.mark.django_db
def test_expiry_worker_never_restores_consumed_invitation(rental_participants):
    owner, tenant, _, property_obj, _ = rental_participants
    lease = Lease.objects.create(
        property=property_obj,
        owner=owner,
        tenant=tenant,
        template_id="eg-residential-v1",
        template_version="1",
        start_date=timezone.localdate(),
        end_date=timezone.localdate() + timedelta(days=30),
        rent_amount_minor=1000000,
    )
    invitation = TenancyInvitation.objects.create(
        property=property_obj,
        owner=owner,
        tenant=tenant,
        expires_at=timezone.now() - timedelta(minutes=1),
        initiated_by=owner,
        status=TenancyInvitation.Status.ACCEPTED,
        lease=lease,
        consumed_at=timezone.now(),
    )

    expire_rental_sources_and_holds.apply().get()

    invitation.refresh_from_db()
    assert invitation.status == TenancyInvitation.Status.ACCEPTED
    assert invitation.lease_id == lease.pk


@pytest.mark.django_db
def test_daily_inventory_lock_rejects_overlap(rental_participants):
    owner, tenant, _, property_obj, offer_id = rental_participants
    starts_on = timezone.localdate() + timedelta(days=10)
    first = Lease.objects.create(
        property=property_obj,
        owner=owner,
        tenant=tenant,
        template_id="eg-residential-v1",
        template_version="1",
        start_date=starts_on,
        end_date=starts_on + timedelta(days=2),
        rent_amount_minor=1000000,
        offer_id=offer_id,
        legacy_read_only=False,
    )
    second = Lease.objects.create(
        property=property_obj,
        owner=owner,
        tenant=tenant,
        template_id="eg-residential-v1",
        template_version="1",
        start_date=starts_on + timedelta(days=1),
        end_date=starts_on + timedelta(days=3),
        rent_amount_minor=1000000,
        offer_id=offer_id,
        legacy_read_only=False,
    )
    expiry = timezone.now() + timedelta(minutes=30)
    reserve_inventory_days(first, first.start_date, first.end_date, expiry)

    with pytest.raises(RentalConflict):
        reserve_inventory_days(second, second.start_date, second.end_date, expiry)


@override_settings(
    DEBUG=False,
    RENTAL_PROVIDER_BACKEND="fake",
    RENTAL_FAKE_PROVIDER_ALLOWED=False,
    RENTAL_RUNTIME_ENVIRONMENT="production",
)
def test_fake_provider_is_forbidden_in_production_settings():
    with pytest.raises(ImproperlyConfigured):
        get_rental_provider()
