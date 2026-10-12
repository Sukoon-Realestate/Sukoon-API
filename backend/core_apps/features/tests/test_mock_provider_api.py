import uuid
from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.features.models import OwnerOnboardingSession, OwnerPaymentProfile
from .test_current_cycle_contract import API, awaiting_signatures, create_checkout, sign
from .test_rental_phase2 import authenticated, rental_participants


@pytest.mark.django_db
def test_same_onboarding_key_is_isolated_between_accounts(rental_participants):
    request_key = str(uuid.uuid4())
    session_ids = []
    for user in (rental_participants[0], rental_participants[2]):
        client = authenticated(user)
        profile = client.get(API + "owner-payment-profile/").data
        response = client.post(
            API + "owner-payment-profile/onboarding-session/",
            {
                "expected_revision": profile["revision"],
                "request_key": request_key,
                "accepted_policy_versions": ["rental-policy-v1"],
            },
            format="json",
        )
        assert response.status_code == 201, response.data
        session_ids.append(
            OwnerOnboardingSession.objects.get(
                id=response.data["session_id"]
            ).provider_session_id
        )
    assert len(set(session_ids)) == 2


@pytest.mark.django_db
def test_mock_signing_scoped_replay_and_expiry(awaiting_signatures):
    owner, tenant, stranger, lease, sessions = awaiting_signatures
    path = API + f"mock-provider/signing-sessions/{sessions[0].id}/complete/"
    body = {"request_key": str(uuid.uuid4()), "expected_revision": lease.revision}
    assert APIClient().post(path, body, format="json").status_code == 401
    for unrelated in (tenant, stranger):
        assert (
            authenticated(unrelated).post(path, body, format="json").status_code == 404
        )
    client = authenticated(owner)
    assert (
        client.post(path, {**body, "expected_revision": 999}, format="json").status_code
        == 409
    )
    result = client.post(path, body, format="json")
    assert result.status_code == 200
    assert result.data["resource"]["provider_mode"] == "mock"
    assert client.post(path, body, format="json").data == result.data
    assert (
        client.post(path, {**body, "expected_revision": 999}, format="json").status_code
        == 409
    )
    sessions[1].expires_at = timezone.now() - timedelta(seconds=1)
    sessions[1].save()
    assert (
        authenticated(tenant)
        .post(
            API + f"mock-provider/signing-sessions/{sessions[1].id}/complete/",
            body,
            format="json",
        )
        .status_code
        == 409
    )
    lease.refresh_from_db()
    assert lease.status == "pending_signatures"
    assert not lease.invoices.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "runtime,allowed,expected",
    [("staging", True, 200), ("staging", False, 404), ("production", True, 404)],
)
def test_mock_requires_explicit_nonproduction_mode(
    rental_participants, runtime, allowed, expected
):
    owner = rental_participants[0]
    client = authenticated(owner)
    profile = client.get(API + "owner-payment-profile/").data
    session = client.post(
        API + "owner-payment-profile/onboarding-session/",
        {
            "expected_revision": profile["revision"],
            "request_key": str(uuid.uuid4()),
            "accepted_policy_versions": ["rental-policy-v1"],
        },
        format="json",
    ).data
    with override_settings(
        RENTAL_RUNTIME_ENVIRONMENT=runtime, RENTAL_FAKE_PROVIDER_ALLOWED=allowed
    ):
        response = client.post(
            session["mock_completion"]["path"],
            {
                "expected_revision": session["mock_completion"]["expected_revision"],
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
    assert response.status_code == expected
    assert OwnerPaymentProfile.objects.get(owner=owner).payout_ready == (
        expected == 200
    )


@pytest.mark.django_db
def test_onboarding_expired_or_replaced_session_cannot_complete(rental_participants):
    owner = rental_participants[0]
    client = authenticated(owner)
    for _ in range(2):
        profile = client.get(API + "owner-payment-profile/").data
        session = client.post(
            API + "owner-payment-profile/onboarding-session/",
            {
                "expected_revision": profile["revision"],
                "request_key": str(uuid.uuid4()),
                "accepted_policy_versions": ["rental-policy-v1"],
            },
            format="json",
        ).data
    old = OwnerOnboardingSession.objects.order_by("created_at").first()
    body = {
        "request_key": str(uuid.uuid4()),
        "expected_revision": session["mock_completion"]["expected_revision"],
    }
    assert (
        client.post(
            API + f"mock-provider/onboarding-sessions/{old.id}/complete/",
            body,
            format="json",
        ).status_code
        == 409
    )
    OwnerOnboardingSession.objects.filter(id=session["session_id"]).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert (
        client.post(session["mock_completion"]["path"], body, format="json").status_code
        == 409
    )
    assert not OwnerPaymentProfile.objects.get(owner=owner).payout_ready


@pytest.mark.django_db
def test_mock_payment_amount_is_server_authoritative_and_payer_scoped(
    awaiting_signatures,
):
    owner, tenant, stranger, lease, sessions = awaiting_signatures
    for session in sessions:
        assert sign(session).status_code == 200
    attempt = create_checkout(tenant, lease.invoices.get())
    path = API + f"mock-provider/payment-attempts/{attempt.id}/events/"
    body = {
        "event": "captured",
        "request_key": str(uuid.uuid4()),
        "expected_revision": attempt.revision,
        "amount_minor": 1,
    }
    for other in (owner, stranger):
        assert authenticated(other).post(path, body, format="json").status_code == 404
    result = authenticated(tenant).post(path, body, format="json")
    assert result.status_code == 200
    assert result.data["resource"]["amount"]["amount_minor"] == 2_000_000
    lease.refresh_from_db()
    assert lease.status == "active"
