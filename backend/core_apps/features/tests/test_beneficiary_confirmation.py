"""Consent to an independently provisioned Test recipient; no payout transport."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import pytest
from django.db import close_old_connections
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.test import APIClient
from core_apps.users.models import User
from core_apps.features.models import (
    OwnerPaymentProfile,
    RentalAuditEvent,
    PaymobPayout,
)
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services import (
    beneficiary_confirmation as service,
    paymob_payout_targets as targets,
)
from core_apps.features.tests import test_paymob_payouts as payout_fixtures

configured = payout_fixtures.configured
pytestmark = pytest.mark.django_db(transaction=True)
URL = "/api/v1/features/v1/owner-payment-profile/"


def api(user):
    result = APIClient()
    result.force_authenticate(user)
    return result


@pytest.fixture
def prepared(configured):
    configured.RENTAL_PROVIDER_BACKEND = "disabled"
    owner = User.objects.create_user(
        email="beneficiary-owner@example.com",
        password="test",
        is_verified=True,
        is_email_verified=True,
    )
    profile = OwnerPaymentProfile.objects.create(owner=owner)
    configured.PAYMOB_PAYOUTS_BENEFICIARIES = {
        "qa-recipient": {
            "profile_id": str(profile.id),
            "profile_revision": profile.revision + 1,
            "verification_reference": "qa-independent-verification",
            "issuer": "vodafone",
            "msisdn": "01020304050",
        }
    }
    return profile, configured


def body(profile):
    return {
        "request_key": str(uuid.uuid4()),
        "expected_revision": profile.revision,
        "accepted_policy_versions": ["rental-policy-v1"],
        "candidate_digest": service.candidate(profile)[2]["digest"],
    }


def test_prepared_recipient_is_private_and_owner_consent_does_not_transfer(prepared):
    profile, config = prepared
    result = api(profile.owner).get(URL)
    assert result.status_code == 200 and result["Cache-Control"] == "private, no-store"
    assert result.data["allowed_actions"] == ["onboard_beneficiary"]
    assert result.data["prepared_beneficiary"]["masked_account"] == "•••• 4050"
    assert "01020304050" not in str(
        result.data
    ) and "verification_reference" not in str(result.data)
    payload = body(profile)
    with patch("core_apps.users.services.sensitive_actions.consume") as consume, patch(
        "core_apps.features.services.paymob_payout_client.transport"
    ) as transport:
        response = api(profile.owner).post(
            URL + "confirm-beneficiary/", payload, format="json"
        )
        assert response.status_code == 200, response.data
        assert (
            api(profile.owner)
            .post(URL + "confirm-beneficiary/", payload, format="json")
            .data
            == response.data
        )
    consume.assert_called_once()
    assert consume.call_args.kwargs["payload"] == payload
    transport.assert_not_called()
    profile.refresh_from_db()
    assert profile.status == "ready" and profile.payout_ready and profile.revision == 2
    assert targets.for_profile(profile)["msisdn"] == "01020304050"
    assert not PaymobPayout.objects.exists()
    assert RentalAuditEvent.objects.filter(action="beneficiary_confirmed").count() == 1
    event = PlanningEvent.objects.get(destination__event_kind="beneficiary_updated")
    assert event.destination["workspace"] == "owner" and service.notification_copy(
        event
    )
    assert not api(profile.owner).get(URL).data["prepared_beneficiary"]


@pytest.mark.parametrize(
    "change",
    [
        "number",
        "channel",
        "evidence",
        "duplicate",
        "revision",
        "restricted",
        "disabled",
        "owner",
        "unverified",
        "frozen",
    ],
)
def test_changed_or_unprepared_recipient_never_becomes_ready(prepared, change):
    profile, config = prepared
    payload = body(profile)
    record = config.PAYMOB_PAYOUTS_BENEFICIARIES["qa-recipient"]
    expected = 503
    if change == "number":
        record["msisdn"] = "01020304051"
        expected = 409
    elif change == "channel":
        config.PAYMOB_PAYOUTS_CHANNEL_EVIDENCE = {}
    elif change == "evidence":
        record["verification_reference"] = ""
    elif change == "duplicate":
        config.PAYMOB_PAYOUTS_BENEFICIARIES["second"] = dict(record)
    elif change == "revision":
        profile.revision += 1
        profile.save()
        expected = 409
    elif change == "restricted":
        profile.status = "restricted"
        profile.save()
    elif change == "disabled":
        config.PAYMOB_PAYOUTS_ENABLED = False
    elif change == "owner":
        record["profile_id"] = str(uuid.uuid4())
    elif change == "unverified":
        User.objects.filter(pk=profile.owner_id).update(is_verified=False)
        expected = 403
    elif change == "frozen":
        User.objects.filter(pk=profile.owner_id).update(sensitive_actions_frozen=True)
        expected = 403
    with patch("core_apps.users.services.sensitive_actions.consume") as consume:
        response = api(profile.owner).post(
            URL + "confirm-beneficiary/", payload, format="json"
        )
    assert response.status_code == expected, response.data
    consume.assert_not_called()
    profile.refresh_from_db()
    assert not profile.payout_ready
    assert not PlanningEvent.objects.exists()


def test_missing_sensitive_proof_and_other_account_are_denied(prepared):
    profile, _ = prepared
    payload = body(profile)
    with patch(
        "core_apps.users.services.sensitive_actions.consume",
        side_effect=PermissionDenied(),
    ):
        assert (
            api(profile.owner)
            .post(URL + "confirm-beneficiary/", payload, format="json")
            .status_code
            == 403
        )
    other = User.objects.create_user(
        email="another-owner@example.com", password="test", is_verified=True
    )
    result = api(other).get(URL)
    assert not result.data["prepared_beneficiary"]
    assert (
        api(other)
        .post(URL + "confirm-beneficiary/", payload, format="json")
        .status_code
        == 503
    )
    profile.refresh_from_db()
    assert not profile.payout_ready


def test_concurrent_confirmations_replay_one_revision(prepared):
    profile, _ = prepared
    payload, owner_id = body(profile), profile.owner_id

    def run():
        close_old_connections()
        try:
            response = api(User.objects.get(pk=owner_id)).post(
                URL + "confirm-beneficiary/", payload, format="json"
            )
            return response.status_code, response.data
        finally:
            close_old_connections()

    with patch(
        "core_apps.users.services.sensitive_actions.consume"
    ) as consume, ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: run(), range(2)))
    assert results[0] == results[1] and results[0][0] == 200
    assert consume.call_count == 1
    profile.refresh_from_db()
    assert profile.revision == 2


def test_bank_recipient_and_current_notification_authority(prepared):
    profile, config = prepared
    record = config.PAYMOB_PAYOUTS_BENEFICIARIES["qa-recipient"]
    record.pop("msisdn")
    record.update(
        issuer="bank_card",
        bank_card_number="EG12345678901234",
        bank_code="CIB",
        full_name="Synthetic Owner",
        bank_transaction_type="cash_transfer",
    )
    preview = api(profile.owner).get(URL).data["prepared_beneficiary"]
    assert (
        preview["channel"] == "bank_card"
        and preview["beneficiary_name"] == "Synthetic Owner"
    )
    with patch("core_apps.users.services.sensitive_actions.consume"):
        assert (
            api(profile.owner)
            .post(URL + "confirm-beneficiary/", body(profile), format="json")
            .status_code
            == 200
        )
    from core_apps.features.services.planning_notifications import (
        deliver_planning_events,
    )

    assert deliver_planning_events(event_kinds=["beneficiary_updated"]) == 1
    event = PlanningEvent.objects.get(destination__event_kind="beneficiary_updated")
    assert service.notification_copy(event)
    User.objects.filter(pk=profile.owner_id).update(is_active=False)
    event.refresh_from_db()
    with pytest.raises(NotFound):
        service.notification_copy(event)


def test_email_otp_confirms_only_the_reviewed_beneficiary(prepared, settings):
    from django.core import mail
    from core_apps.users.tests import test_totp_recovery as assurance
    from core_apps.users.services import sensitive_actions
    from core_apps.users.models import SensitiveAuthorization

    assurance.actors.__wrapped__(settings)
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    profile, _ = prepared
    User.objects.filter(pk=profile.owner_id).update(is_email_verified=True)
    owner = User.objects.get(pk=profile.owner_id)
    session = assurance.request(owner)
    payload = body(profile)
    with patch(
        "core_apps.users.services.assurance.generate_otp", return_value="123456"
    ):
        challenge = sensitive_actions.begin(
            session,
            {
                "action": "beneficiary.onboarding",
                "resource_id": str(profile.id),
                "resource_revision": profile.revision,
                "payload": payload,
            },
        )
    assert mail.outbox[-1].to == [owner.email]
    with pytest.raises(PermissionDenied):
        sensitive_actions.verify(session, challenge["id"], "000000")
    proof = sensitive_actions.verify(session, challenge["id"], "123456")
    caller = APIClient()
    caller.credentials(
        HTTP_AUTHORIZATION=f"Bearer {session.auth}",
        HTTP_X_SOKOUN_AUTHORIZATION=proof["proof"],
    )
    with patch("core_apps.features.services.paymob_payout_client.transport") as send:
        result = caller.post(URL + "confirm-beneficiary/", payload, format="json")
        assert result.status_code == 200, result.data
        assert (
            caller.post(URL + "confirm-beneficiary/", payload, format="json").data
            == result.data
        )
    send.assert_not_called()
    assert SensitiveAuthorization.objects.get(id=challenge["id"]).consumed_at
    profile.refresh_from_db()
    assert profile.payout_ready


def test_missing_email_verification_keeps_the_right_action_blocked(prepared):
    profile, _ = prepared
    User.objects.filter(pk=profile.owner_id).update(is_email_verified=False)
    user = User.objects.get(pk=profile.owner_id)
    assert service.preview(profile, user)
    assert not service.can_confirm(profile, user)
    response = api(user).get(URL)
    assert response.data["allowed_actions"] == []
