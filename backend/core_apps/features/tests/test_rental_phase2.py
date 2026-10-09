import uuid
from datetime import timedelta

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.features.models import (
    Lease,
    OwnerOnboardingSession,
    OwnerPaymentProfile,
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
    session = OwnerOnboardingSession.objects.get(id=session_response.data["session_id"])
    payload = {
        "type": "onboarding.completed",
        "provider_session_id": session.provider_session_id,
    }
    webhook = APIClient().post(
        "/api/v1/features/v1/provider-webhooks/rental/",
        payload,
        format="json",
        HTTP_X_RENTAL_SIGNATURE=sign_fake_webhook(payload),
    )
    assert webhook.status_code == 200
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
    profile = complete_owner_onboarding(owner)
    assert profile.status == OwnerPaymentProfile.Status.READY
    assert profile.masked_beneficiary == {"account_last4": "4242"}

    starts_on = timezone.localdate() + timedelta(days=10)
    ends_on = starts_on + timedelta(days=31)
    tenant_client = authenticated(tenant)
    owner_client = authenticated(owner)

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
        sessions.append(SigningSession.objects.get(id=response.data["session_id"]))

    for session in sessions:
        payload = {
            "type": "signature.completed",
            "provider_session_id": session.provider_session_id,
        }
        response = APIClient().post(
            "/api/v1/features/v1/provider-webhooks/rental/",
            payload,
            format="json",
            HTTP_X_RENTAL_SIGNATURE=sign_fake_webhook(payload),
        )
        assert response.status_code == 200

    activated = Lease.objects.get(id=lease["id"])
    assert activated.status == Lease.Status.ACTIVE
    assert activated.activated_at is not None
    assert set(
        RentalInventoryDayLock.objects.filter(lease=activated).values_list(
            "kind", flat=True
        )
    ) == {RentalInventoryDayLock.Kind.OCCUPIED}


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
