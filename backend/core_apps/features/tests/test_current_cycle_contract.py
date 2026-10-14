"""Regressions from the actual Flutter owner/tenant cycle contracts."""

import uuid
from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.features.models import (
    DepositAgreement,
    IdempotencyRecord,
    Lease,
    OwnerOnboardingSession,
    OwnerPaymentProfile,
    PaymentAttempt,
    RentalInventoryDayLock,
    RentInvoice,
    SigningSession,
    TenancyInvitation,
)
from core_apps.features.providers import get_rental_provider, sign_fake_webhook
from core_apps.features.services.rental_phase2 import reserve_inventory_days
from core_apps.features.services.rental_phase6 import closure_blocking_reasons
from core_apps.features.tasks import (
    expire_rental_sources_and_holds,
    run_rental_billing_cycle,
)
from .test_rental_phase2 import (
    agreement_terms,
    authenticated,
    complete_owner_onboarding,
    rental_participants,
)

API = "/api/v1/features/v1/"


@pytest.fixture
def awaiting_signatures(rental_participants):
    owner, tenant, stranger, prop, offer_id = rental_participants
    complete_owner_onboarding(owner)
    starts = timezone.localdate() + timedelta(days=10)
    ends = starts + timedelta(days=60)
    terms = agreement_terms(starts, ends)
    lease = Lease.objects.create(
        property=prop,
        owner=owner,
        tenant=tenant,
        offer_id=offer_id,
        offer_snapshot={"rental_scope": "entire_property", "offer_id": offer_id},
        template_id="eg-residential-v1",
        template_version="1",
        start_date=starts,
        end_date=ends,
        rent_amount_minor=1_000_000,
        status=Lease.Status.PENDING_SIGNATURES,
        legacy_read_only=False,
        terms=terms,
        policy_version="rental-policy-v1",
        document_id=uuid.uuid4(),
        document_hash="a" * 64,
        hold_expires_at=timezone.now() + timedelta(minutes=30),
    )
    reserve_inventory_days(lease, starts, ends, lease.hold_expires_at)
    sessions = []
    for user in (owner, tenant):
        response = authenticated(user).post(
            API + f"leases/{lease.id}/signing-session/",
            {
                "document_id": str(lease.document_id),
                "document_hash": lease.document_hash,
                "expected_revision": lease.revision,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        assert response.status_code == 201
        sessions.append(SigningSession.objects.get(id=response.data["session_id"]))
    return owner, tenant, stranger, lease, sessions


def sign(session):
    payload = {
        "type": "signature.completed",
        "provider_session_id": session.provider_session_id,
    }
    return APIClient().post(
        API + "provider-webhooks/rental/",
        payload,
        format="json",
        HTTP_X_RENTAL_SIGNATURE=sign_fake_webhook(payload),
    )


def create_checkout(tenant, invoice):
    client = authenticated(tenant)
    quote = client.post(
        API + f"rent-invoices/{invoice.id}/quote/",
        {
            "decision": "quote",
            "expected_revision": invoice.revision,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert quote.status_code == 201, quote.data
    body = {
        "invoice_id": str(invoice.id),
        "quote_id": quote.data["resource"]["quote_id"],
        "expected_revision": invoice.revision,
        "request_key": str(uuid.uuid4()),
    }
    response = client.post(
        API + f"rent-invoices/{invoice.id}/checkout/", body, format="json"
    )
    assert response.status_code == 201, response.data
    return PaymentAttempt.objects.get(
        id=response.data["resource"]["payment_attempt_id"]
    )


def capture(attempt, amount=None):
    payload = {
        "event_id": "capture-" + str(attempt.id),
        "type": "payment.captured",
        "sequence": 1,
        "payment_attempt_id": str(attempt.id),
        "amount_minor": amount if amount is not None else attempt.amount_minor,
        "currency": "EGP",
    }
    return APIClient().post(
        API + "provider-webhooks/payments/",
        payload,
        format="json",
        HTTP_X_RENTAL_SIGNATURE=sign_fake_webhook(payload),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query",
    [
        "",
        "?action=anything",
        "?capability=lifestyle&action=save",
        "?capability=housing_groups&action=create",
    ],
)
@override_settings(PLANNING_ENABLED_SERVICES=[])
def test_disabled_planning_never_grants_actions(rental_participants, query):
    response = authenticated(rental_participants[1]).get(
        API + "planning-capabilities/" + query, HTTP_ACCEPT_LANGUAGE="ar"
    )
    assert response.status_code == 200
    assert (
        response.data["allowed_actions"]
        == response.data["verified_services"]
        == response.data["enabled_capabilities"]
        == []
    )
    assert response.data["expires_at"] is None
    assert response["Content-Language"] == "ar"
    assert any("التخطيط" in reason for reason in response.data["blocking_reasons"])


@pytest.mark.django_db
@override_settings(RENTAL_PROVIDER_BACKEND="disabled", RENTAL_CHECKOUT_ENABLED=True)
def test_disabled_provider_has_no_onboarding_grants_or_server_error(
    rental_participants,
):
    owner = rental_participants[0]
    client = authenticated(owner)
    profile = client.get(API + "owner-payment-profile/").data
    assert profile["allowed_actions"] == []
    grant = client.get(
        API
        + f"rental-capabilities/?subject_id={profile['id']}&action=onboard_beneficiary"
    )
    assert grant.data["allowed_actions"] == []
    response = client.post(
        API + "owner-payment-profile/onboarding-session/",
        {
            "expected_revision": profile["revision"],
            "request_key": str(uuid.uuid4()),
            "accepted_policy_versions": ["rental-policy-v1"],
        },
        format="json",
    )
    assert response.status_code == 403
    assert response["X-App-Error-Code"] == "capability_unavailable"
    assert not OwnerOnboardingSession.objects.exists()


@pytest.mark.django_db
def test_unverified_actor_has_no_grants_and_cannot_onboard(rental_participants):
    owner = rental_participants[0]
    owner.is_verified = False
    owner.save()
    client = authenticated(owner)
    profile = client.get(API + "owner-payment-profile/").data
    grant = client.get(
        API
        + f"rental-capabilities/?subject_id={profile['id']}&action=onboard_beneficiary"
    ).data
    assert (
        grant["enabled_capabilities"]
        == grant["allowed_actions"]
        == profile["allowed_actions"]
        == []
    )
    response = client.post(
        API + "owner-payment-profile/onboarding-session/",
        {
            "expected_revision": 1,
            "request_key": str(uuid.uuid4()),
            "accepted_policy_versions": ["rental-policy-v1"],
        },
        format="json",
    )
    assert response.status_code == 403
    assert not OwnerOnboardingSession.objects.exists()


@pytest.mark.django_db
def test_second_signature_issues_one_invoice_and_never_creates_charge_on_get(
    awaiting_signatures,
):
    owner, tenant, stranger, lease, sessions = awaiting_signatures
    assert sign(sessions[0]).status_code == 200
    assert not lease.invoices.exists()
    assert not DepositAgreement.objects.filter(lease=lease).exists()
    assert (
        authenticated(tenant).get(API + f"leases/{lease.id}/deposit/").status_code
        == 404
    )
    assert not lease.invoices.exists()
    assert sign(sessions[1]).status_code == 200
    lease.refresh_from_db()
    deadline = lease.hold_expires_at
    assert sign(sessions[1]).status_code == 200
    lease.refresh_from_db()
    assert lease.hold_expires_at == deadline
    assert lease.status == Lease.Status.SIGNED and lease.activated_at is None
    invoice = lease.invoices.get()
    before = (lease.revision, invoice.revision, invoice.lines.count())
    for user in (owner, tenant):
        client = authenticated(user)
        for suffix in ("", "rental-center/", "deposit/"):
            assert client.get(API + f"leases/{lease.id}/" + suffix).status_code == 200
    lease.refresh_from_db()
    invoice.refresh_from_db()
    assert before == (lease.revision, invoice.revision, invoice.lines.count())
    assert lease.invoices.count() == 1
    assert (
        authenticated(stranger).get(API + f"rent-invoices/{invoice.id}/").status_code
        == 404
    )
    assert (
        authenticated(owner).get(API + f"rent-invoices/{invoice.id}/").data["can_pay"]
        is False
    )


@pytest.mark.django_db
def test_expired_payment_hold_releases_inventory_but_retains_late_capture(
    awaiting_signatures,
):
    owner, tenant, _, lease, sessions = awaiting_signatures
    for session in sessions:
        assert sign(session).status_code == 200
    invoice = lease.invoices.get()
    attempt = create_checkout(tenant, invoice)
    before = timezone.now() - timedelta(seconds=1)
    Lease.objects.filter(pk=lease.pk).update(hold_expires_at=before)
    lease.inventory_day_locks.update(expires_at=before)
    assert expire_rental_sources_and_holds()["expired_agreements"] == 1
    assert expire_rental_sources_and_holds()["expired_agreements"] == 0
    assert not lease.inventory_day_locks.exists()
    response = capture(attempt)
    assert response.status_code == 200, response.data
    attempt.refresh_from_db()
    lease.refresh_from_db()
    assert attempt.payment_status == "captured"
    assert attempt.failure_code == "activation_review_required"
    assert lease.status == Lease.Status.EXPIRED and lease.activated_at is None
    assert lease.financial_closure_status != Lease.FinancialClosureStatus.CLOSED
    assert (
        authenticated(tenant).get(API + f"rent-invoices/{invoice.id}/").data["can_pay"]
        is False
    )
    lease.billing_periods.filter(sequence=2).update(issue_at=before)
    run_rental_billing_cycle()
    assert lease.invoices.count() == 1


@pytest.mark.django_db
def test_wrong_capture_cannot_activate_or_allocate_money(awaiting_signatures):
    _, tenant, _, lease, sessions = awaiting_signatures
    for session in sessions:
        assert sign(session).status_code == 200
    invoice = lease.invoices.get()
    attempt = create_checkout(tenant, invoice)
    assert capture(attempt, amount=invoice.amount_minor - 1).status_code == 409
    lease.refresh_from_db()
    invoice.refresh_from_db()
    assert lease.status == "signed" and invoice.applied_minor == 0
    assert not attempt.ledger_transactions.exists()


@pytest.mark.django_db
def test_cancel_receipt_matches_collection_before_detail_and_read_is_side_effect_free(
    rental_participants,
):
    owner, tenant, _, prop, _ = rental_participants
    start = timezone.localdate() + timedelta(days=5)
    lease = Lease.objects.create(
        property=prop,
        owner=owner,
        tenant=tenant,
        template_id="eg-residential-v1",
        template_version="1",
        start_date=start,
        end_date=start + timedelta(days=30),
        rent_amount_minor=1000000,
        legacy_read_only=False,
    )
    path = API + f"leases/{lease.id}/"
    body = {"revision": lease.revision, "request_key": str(uuid.uuid4())}
    response = authenticated(owner).post(path + "cancel/", body, format="json")
    assert response.status_code == 200
    receipt = response.data
    assert receipt["status"] == receipt["lease_status"] == "cancelled"
    assert receipt["financial_closure_status"] == "closed"
    assert receipt["revision"] == body["revision"] + 1
    for actor, workspace in ((owner, "owner"), (tenant, "tenant")):
        client = authenticated(actor)
        collection = client.get(API + f"leases/?workspace={workspace}").data["results"]
        row = next(x for x in collection if x["id"] == str(lease.id))
        for key in (
            "revision",
            "status",
            "occupancy_status",
            "financial_closure_status",
        ):
            assert row[key] == receipt[key]
        for suffix in ("", "rental-center/", ""):
            assert client.get(path + suffix).data["revision"] == receipt["revision"]
    assert (
        authenticated(owner).post(path + "cancel/", body, format="json").data == receipt
    )
    # Old stale data must be repaired explicitly, never by whichever GET runs first.
    Lease.objects.filter(pk=lease.pk).update(financial_closure_status="open")
    for suffix in ("", "rental-center/"):
        assert (
            authenticated(owner).get(path + suffix).data["financial_closure_status"]
            == "open"
        )


@pytest.mark.django_db
def test_pending_payment_blocks_closure_even_if_invoice_was_cancelled(
    awaiting_signatures,
):
    _, tenant, _, lease, sessions = awaiting_signatures
    for session in sessions:
        assert sign(session).status_code == 200
    invoice = lease.invoices.get()
    create_checkout(tenant, invoice)
    invoice.status = RentInvoice.Status.CANCELLED
    invoice.save()
    lease.status = Lease.Status.CANCELLED
    lease.save()
    assert "A payment is still awaiting reconciliation." in closure_blocking_reasons(
        lease
    )


@pytest.mark.django_db
def test_masked_beneficiary_never_serializes_full_account_number(rental_participants):
    owner = rental_participants[0]
    OwnerPaymentProfile.objects.create(
        owner=owner,
        masked_beneficiary={
            "account_number": "1234567891234567",
            "bank_name": "QA Bank",
        },
    )
    response = authenticated(owner).get(API + "owner-payment-profile/")
    assert response.data["masked_beneficiary"] == "QA Bank •••• 4567"


@pytest.mark.django_db
@pytest.mark.parametrize("initial_revision", [1, 7])
def test_structured_cancel_uses_flutter_body_and_canonical_receipt(
    rental_participants, initial_revision
):
    owner, tenant, _, prop, _ = rental_participants
    starts = timezone.localdate() + timedelta(days=7)
    lease = Lease.objects.create(
        property=prop,
        owner=owner,
        tenant=tenant,
        template_id="eg-residential-v1",
        template_version="1",
        start_date=starts,
        end_date=starts + timedelta(days=30),
        rent_amount_minor=1000000,
        legacy_read_only=False,
        revision=initial_revision,
    )
    body = {
        "decision": "cancel_draft",
        "expected_revision": initial_revision,
        "request_key": str(uuid.uuid4()),
        "note": "",
    }
    url = API + f"leases/{lease.id}/cancel/"
    result = authenticated(owner).post(url, body, format="json")
    assert result.status_code == 200
    assert result.data["resource"]["status"] == "cancelled"
    assert result.data["resource"]["financial_closure_status"] == "closed"
    assert result.data["resource"]["revision"] == initial_revision + 1
    assert result.data["operation_receipt"]["revision"] == initial_revision + 1
    assert result.data["operation_receipt"]["request_key"] == body["request_key"]
    assert authenticated(owner).post(url, body, format="json").data == result.data
    lease.refresh_from_db()
    assert lease.revision == initial_revision + 1
    assert (
        IdempotencyRecord.objects.get(operation="lease.cancel").result_revision
        == lease.revision
    )
