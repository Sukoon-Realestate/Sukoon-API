"""Staging transport contract and financial recovery; no external transfers."""

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.db import close_old_connections, connection, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, NotFound

from core_apps.admin_api.models import StaffProfile
from core_apps.users.models import User, StaffSecurityIdentity, TotpRecoveryRequest
from core_apps.features.models import (
    LedgerTransaction,
    OwnerPaymentProfile,
    OwnerPayable,
    PaymentAttempt,
    PaymentQuote,
    RentInvoice,
    RentalPayout,
    PaymobPayout,
    PayoutBatch,
    PayoutAuditEvent,
    RentalOperationalCase,
    RefundRequest,
)
from core_apps.features.services import paymob_payouts as service
from core_apps.features.services import paymob_payout_client as client
from core_apps.features.services import paymob_payout_targets as targets
from core_apps.features.services.rental_lifecycle.provider_instructions import (
    execute_local_instruction,
)
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.tests import test_rental_phase4 as fixtures

phase4_lease = fixtures.phase4_lease
client_for = fixtures.client_for

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def configured(settings):
    settings.PAYMOB_PAYOUTS_ENABLED = True
    settings.PAYMOB_PAYOUTS_CLIENT_ID = "test-client"
    settings.PAYMOB_PAYOUTS_CLIENT_SECRET = "synthetic-secret"
    settings.PAYMOB_PAYOUTS_USERNAME = "test-merchant"
    settings.PAYMOB_PAYOUTS_PASSWORD = "synthetic-password"
    settings.PAYMOB_PAYOUTS_STAGING_EVIDENCE = "qa-account-provisioned"
    settings.PAYMOB_PAYOUTS_CHANNEL_EVIDENCE = {
        "vodafone": "qa-wallet",
        "bank_card": "qa-bank",
    }
    settings.PAYMOB_PAYOUTS_BENEFICIARIES = {}
    return settings


@pytest.fixture
def instruction(phase4_lease, configured):
    owner, tenant, lease = phase4_lease
    operator = User.objects.create_user(
        email="payout-operator@example.com", password="pass", is_verified=True
    )
    StaffProfile.objects.create(user=operator, role_name="payout_operator")
    profile = OwnerPaymentProfile.objects.create(
        owner=owner,
        status="ready",
        payout_ready=True,
        provider=client.PROVIDER,
        provider_account_id="qa-recipient",
        masked_beneficiary={"account_last4": "4050"},
    )
    configured.PAYMOB_PAYOUTS_BENEFICIARIES = {
        "qa-recipient": {
            "profile_id": str(profile.id),
            "profile_revision": profile.revision,
            "verification_reference": "qa-recipient-verified",
            "issuer": "vodafone",
            "msisdn": "01020304050",
        }
    }
    invoice = RentInvoice.objects.create(
        lease=lease,
        reference="PAYOUT-QA",
        due_date=lease.start_date,
        amount_minor=12345,
        charges_minor=12345,
        applied_minor=12345,
        status="paid",
    )
    quote = PaymentQuote.objects.create(
        invoice=invoice,
        request_key=uuid.uuid4(),
        invoice_revision=1,
        payer_amount_minor=12345,
        policy_version="rental-policy-v1",
        fingerprint="a" * 64,
        expires_at=timezone.now() + timedelta(minutes=20),
    )
    attempt = PaymentAttempt.objects.create(
        invoice=invoice,
        payer=tenant,
        quote=quote,
        request_key=uuid.uuid4(),
        invoice_revision=1,
        policy_version="rental-policy-v1",
        quote_fingerprint=quote.fingerprint,
        payment_status="captured",
        amount_minor=12345,
        settlement_status="settled",
    )
    payable = OwnerPayable.objects.create(
        lease=lease,
        invoice=invoice,
        payment_attempt=attempt,
        gross_minor=12345,
        net_minor=12345,
        settlement_status="settled",
        payout_status="submitted",
    )
    batch = PayoutBatch.objects.create(approved_by=operator, request_key=uuid.uuid4())
    payout = RentalPayout.objects.create(
        batch=batch,
        owner=owner,
        lease=lease,
        amount_minor=12345,
        beneficiary_profile_revision=profile.revision,
        beneficiary_provider=profile.provider,
        beneficiary_account_id=profile.provider_account_id,
        masked_beneficiary=profile.masked_beneficiary,
    )
    payout.payables.add(payable)
    with transaction.atomic():
        item = service.stage(payout, targets.for_profile(profile))
    return item


def proof(item, **changes):
    return {
        **targets.unseal(item),
        "transaction_id": str(uuid.uuid4()),
        "amount": "123.45",
        "disbursement_status": "successful",
        "status_code": "200",
        "client_transaction_reference": str(item.reference),
        **changes,
    }


def transport_for(item, *, submit=None, inquiry=None):
    def transport(path, payload, **kwargs):
        assert not connection.in_atomic_block
        if path == "/api/secure/o/token/":
            return {"access_token": "synthetic-token", "token_type": "Bearer"}
        if path == "/api/secure/disburse/":
            assert payload["client_reference_id"] == str(item.reference)
            assert payload["amount"] == 123.45
            assert payload["customer_bears_fees"] is False
            if isinstance(submit, Exception):
                raise submit
            return submit if submit is not None else proof(item)
        assert path == "/api/secure/transaction/inquire/by-reference/"
        assert kwargs["method"] == "GET"
        assert payload["references_list"] == [str(item.reference)]
        return (
            inquiry
            if inquiry is not None
            else {"count": 1, "next": None, "results": [proof(item)]}
        )

    return transport


def test_wallet_success_accounts_once_and_never_exposes_recipient(instruction):
    with patch.object(
        client, "transport", side_effect=transport_for(instruction)
    ) as network:
        assert service.process(instruction).status == "paid"
        assert service.process(instruction).status == "paid"
    assert (
        len(
            [
                call
                for call in network.call_args_list
                if call.args[0].endswith("disburse/")
            ]
        )
        == 1
    )
    assert (
        LedgerTransaction.objects.get(
            reference=f"payout:{instruction.payout.id}"
        ).entries.count()
        == 2
    )
    assert (
        PayoutAuditEvent.objects.filter(
            payout=instruction.payout, action="paid"
        ).count()
        == 1
    )
    instruction.refresh_from_db()
    assert "01020304050" not in instruction.recipient_ciphertext
    detail = client_for(instruction.payout.owner).get(
        f"/api/v1/features/v1/payouts/{instruction.payout.id}/"
    )
    assert detail.status_code == 200
    assert "01020304050" not in json.dumps(detail.data)


def test_timeout_empty_inquiry_keeps_original_then_recovers(instruction):
    with patch.object(
        client,
        "transport",
        side_effect=transport_for(instruction, submit=TimeoutError()),
    ):
        with pytest.raises(client.PayoutUnavailable):
            service.process(instruction)
    with patch.object(
        client,
        "transport",
        side_effect=transport_for(
            instruction, inquiry={"count": 0, "next": None, "results": []}
        ),
    ) as network:
        for _ in range(2):
            with pytest.raises(client.PayoutUnavailable):
                service.process(instruction)
    assert not any(
        call.args[0].endswith("disburse/") for call in network.call_args_list
    )
    assert RentalOperationalCase.objects.filter(payout=instruction.payout).count() == 1
    assert not LedgerTransaction.objects.filter(
        reference=f"payout:{instruction.payout.id}"
    ).exists()
    # A later beneficiary edit and a factor restriction cannot rewrite already
    # executed money. Inquiry uses the encrypted original, not today's profile.
    OwnerPaymentProfile.objects.filter(owner=instruction.payout.owner).update(
        revision=2, provider_account_id="different"
    )
    User.objects.filter(pk=instruction.payout.batch.approved_by_id).update(
        sensitive_actions_frozen=True
    )
    with patch.object(
        client, "transport", side_effect=transport_for(instruction)
    ) as network:
        assert service.process(instruction).status == "paid"
    assert not any(
        call.args[0].endswith("disburse/") for call in network.call_args_list
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"amount": "123.46"},
        {"msisdn": "01000000000"},
        {"issuer": "etisalat"},
        {"client_transaction_reference": "wrong"},
        {"amount": True},
        {"amount": "NaN"},
        {"currency": "USD"},
        {"customer_bears_fees": True},
        {"transaction_id": ""},
    ],
)
def test_mismatched_provider_result_is_not_money_proof(instruction, changes):
    with patch.object(
        client,
        "transport",
        side_effect=transport_for(instruction, submit=proof(instruction, **changes)),
    ):
        with pytest.raises(client.PayoutUnavailable):
            service.process(instruction)
    instruction.refresh_from_db()
    assert instruction.status == "unknown"
    assert not LedgerTransaction.objects.exists()


def test_bank_pending_is_not_paid_then_matching_inquiry_confirms(
    instruction, configured
):
    profile = OwnerPaymentProfile.objects.get(owner=instruction.payout.owner)
    recipient = {
        "issuer": "bank_card",
        "bank_code": "BOA",
        "bank_card_number": "111122244050",
        "full_name": "QA Recipient",
        "bank_transaction_type": "cash_transfer",
    }
    configured.PAYMOB_PAYOUTS_BENEFICIARIES["qa-recipient"].update(recipient)
    instruction.recipient_ciphertext = targets.seal(recipient)
    instruction.recipient_digest = service.fingerprint(recipient)
    instruction.save()
    assert targets.for_profile(profile) == recipient
    pending = proof(instruction, disbursement_status="pending", status_code="8000")
    with patch.object(
        client, "transport", side_effect=transport_for(instruction, submit=pending)
    ):
        assert service.process(instruction).status == "processing"
    assert not LedgerTransaction.objects.exists()
    final = {**pending, "disbursement_status": "successful", "status_code": "200"}
    with patch.object(
        client,
        "transport",
        side_effect=transport_for(
            instruction, inquiry={"count": 1, "next": None, "results": [final]}
        ),
    ) as network:
        assert service.process(instruction).status == "paid"
    query = next(call for call in network.call_args_list if "inquire" in call.args[0])
    assert query.args[1]["bank_transactions"] is True


def test_provisioning_is_separate_from_collection_and_channel_specific(configured):
    configured.PAYMOB_PAYOUTS_PASSWORD = ""
    assert not client.ready("vodafone", submission=True)
    configured.PAYMOB_PAYOUTS_PASSWORD = "synthetic-password"
    assert client.ready("vodafone", submission=True)
    assert not client.ready("bank_wallet", submission=True)
    configured.RENTAL_RUNTIME_ENVIRONMENT = "production"
    assert not client.ready()


def test_recovery_request_then_completion_never_automatically_sends(instruction):
    actor = instruction.payout.batch.approved_by
    identity = StaffSecurityIdentity.objects.create(
        user=actor,
        person_reference="qa-person",
        evidence_reference="qa-identity",
        known_channel_reference="qa-channel",
    )
    recovery = TotpRecoveryRequest.objects.create(
        user=actor,
        identity=identity,
        person_reference=identity.person_reference,
        reason="Lost factor",
    )
    # Even if the worker was stopped throughout recovery, its old authorization
    # must not resume when the recovery becomes inactive.
    recovery.active, recovery.status = False, "completed"
    recovery.save()
    with patch.object(
        client, "transport", side_effect=transport_for(instruction)
    ) as network:
        assert service.process(instruction).status == "held"
        assert service.process(instruction).status == "held"
    assert not any(
        call.args[0].endswith("disburse/") for call in network.call_args_list
    )
    instruction.refresh_from_db()
    assert instruction.failure_code == "authorization_changed"


def test_changed_beneficiary_and_pending_refund_block_dispatch(instruction, configured):
    configured.PAYMOB_PAYOUTS_BENEFICIARIES["qa-recipient"]["msisdn"] = "01099994050"
    with patch.object(
        client, "transport", side_effect=transport_for(instruction)
    ) as network:
        assert service.process(instruction).status == "held"
    assert not any(
        call.args[0].endswith("disburse/") for call in network.call_args_list
    )


def test_pending_refund_reserves_payout_balance(instruction):
    payable = instruction.payout.payables.get()
    RefundRequest.objects.create(
        lease=instruction.payout.lease,
        payment_attempt=payable.payment_attempt,
        requester=payable.payment_attempt.payer,
        amount_minor=100,
        refundable_balance_snapshot_minor=12345,
        reason="QA",
        request_key=uuid.uuid4(),
    )
    with patch.object(
        client, "transport", side_effect=transport_for(instruction)
    ) as network:
        assert service.process(instruction).status == "held"
    assert not any(
        call.args[0].endswith("disburse/") for call in network.call_args_list
    )


def test_confirmed_failure_is_held_without_automatic_second_transfer(instruction):
    with patch.object(
        client,
        "transport",
        side_effect=transport_for(
            instruction,
            submit=proof(instruction, disbursement_status="failed", status_code="500"),
        ),
    ) as network:
        assert service.process(instruction).status == "held"
        assert service.process(instruction).status == "held"
    assert (
        len(
            [
                call
                for call in network.call_args_list
                if call.args[0].endswith("disburse/")
            ]
        )
        == 1
    )
    assert not LedgerTransaction.objects.exists()


def test_concurrent_workers_claim_one_instruction(instruction):
    def claim():
        close_old_connections()
        try:
            return service.claim(instruction.pk) is not None
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: claim(), range(2))) == [False, True]
    assert (
        PayoutAuditEvent.objects.filter(
            payout=instruction.payout, action="submitted"
        ).count()
        == 1
    )


def test_reconcile_endpoint_cannot_dispatch_queued_payout(instruction):
    with patch.object(client, "transport") as network:
        response = client_for(instruction.payout.batch.approved_by).post(
            f"/api/v1/features/v1/operations/payouts/{instruction.payout.id}/reconcile/",
            {"request_key": str(uuid.uuid4())},
            format="json",
        )
    assert response.status_code == 200, response.data
    network.assert_not_called()
    assert response.data["resource"]["status"] == "created"


def test_paymob_payout_never_uses_local_fake_success(instruction):
    with transaction.atomic(), pytest.raises(RentalConflict):
        execute_local_instruction(
            kind="payout",
            subject=instruction.payout,
            request_key=instruction.payout.batch.request_key,
            payload={},
        )


def test_http_uses_staging_form_auth_and_bounded_nonredirecting_transport(configured):
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.read.return_value = b'{"access_token":"qa-token","token_type":"Bearer"}'
    opener = Mock()
    opener.open.return_value = response
    with patch.object(client, "build_opener", return_value=opener) as build:
        assert client.token() == "qa-token"
    request = opener.open.call_args.args[0]
    assert request.full_url == client.HOST + "/api/secure/o/token/"
    assert b"grant_type=password" in request.data
    assert request.get_header("Content-type") == "application/x-www-form-urlencoded"
    assert isinstance(build.call_args.args[0], client.NoRedirect)


def test_unsent_approval_needs_fresh_authorization_and_replays_once(instruction):
    actor = instruction.payout.batch.approved_by
    User.objects.filter(pk=actor.pk).update(security_epoch=1)
    with patch.object(client, "transport", side_effect=transport_for(instruction)):
        assert service.process(instruction).status == "held"
    payout = RentalPayout.objects.get(pk=instruction.payout_id)
    path = f"/api/v1/features/v1/operations/payouts/{payout.id}/reauthorize/"
    data = {"request_key": str(uuid.uuid4()), "expected_revision": payout.revision}
    with patch(
        "core_apps.users.services.sensitive_actions.consume",
        side_effect=PermissionDenied(),
    ):
        assert client_for(actor).post(path, data, format="json").status_code == 403
    instruction.refresh_from_db()
    assert instruction.status == "held"
    # The explicit isolated test verifier accepts a NEW exact approval. Merely
    # completing recovery above never queued the old approval again.
    response = client_for(actor).post(path, data, format="json")
    assert response.status_code == 200, response.data
    assert client_for(actor).post(path, data, format="json").data == response.data
    assert (
        PayoutAuditEvent.objects.filter(payout=payout, action="reauthorized").count()
        == 1
    )
    with patch.object(client, "transport", side_effect=transport_for(instruction)):
        assert service.process(instruction).status == "paid"


def test_unknown_instruction_cannot_be_reauthorized_or_switched(instruction):
    with patch.object(
        client,
        "transport",
        side_effect=transport_for(instruction, submit=TimeoutError()),
    ):
        with pytest.raises(client.PayoutUnavailable):
            service.process(instruction)
    payout = RentalPayout.objects.get(pk=instruction.payout_id)
    actor = payout.batch.approved_by
    response = client_for(actor).post(
        f"/api/v1/features/v1/operations/payouts/{payout.id}/reauthorize/",
        {"request_key": str(uuid.uuid4()), "expected_revision": payout.revision},
        format="json",
    )
    assert response.status_code == 409
    instruction.refresh_from_db()
    assert instruction.status == "unknown"


def test_frozen_operator_can_only_reconcile_original_provider_result(instruction):
    with patch.object(
        client,
        "transport",
        side_effect=transport_for(instruction, submit=TimeoutError()),
    ):
        with pytest.raises(client.PayoutUnavailable):
            service.process(instruction)
    actor = instruction.payout.batch.approved_by
    User.objects.filter(pk=actor.pk).update(sensitive_actions_frozen=True)
    review = client_for(actor).get(
        f"/api/v1/features/v1/operations/payouts/{instruction.payout.id}/review/"
    )
    assert review.status_code == 200 and review.data["allowed_actions"] == ["reconcile"]
    with patch.object(
        client, "transport", side_effect=transport_for(instruction)
    ) as network:
        response = client_for(actor).post(
            f"/api/v1/features/v1/operations/payouts/{instruction.payout.id}/reconcile/",
            {"request_key": str(uuid.uuid4())},
            format="json",
        )
    assert response.status_code == 200, response.data
    assert response.data["resource"]["status"] == "paid"
    assert not any(
        call.args[0].endswith("disburse/") for call in network.call_args_list
    )


def test_account_change_and_duplicate_reference_results_do_not_confirm(
    instruction, configured
):
    service.claim(instruction.pk)
    configured.PAYMOB_PAYOUTS_USERNAME = "another-account"
    with patch.object(client, "transport") as network, pytest.raises(
        client.PayoutUnavailable
    ):
        service.process(instruction)
    network.assert_not_called()
    configured.PAYMOB_PAYOUTS_USERNAME = "test-merchant"
    duplicate = {
        "count": 2,
        "next": None,
        "results": [proof(instruction), proof(instruction)],
    }
    with patch.object(
        client, "transport", side_effect=transport_for(instruction, inquiry=duplicate)
    ), pytest.raises(client.PayoutUnavailable):
        service.process(instruction)
    assert not LedgerTransaction.objects.exists()


def test_http_is_forbidden_inside_business_transaction(instruction):
    with transaction.atomic(), patch.object(
        client, "transport"
    ) as network, pytest.raises(RuntimeError):
        service.process(instruction)
    network.assert_not_called()


def test_execute_stages_exact_bound_target_once_and_returns_owner_safe_projection(
    instruction,
):
    from core_apps.features.models import RentalHandover
    from core_apps.users.services.sensitive_actions import consume

    payout = instruction.payout
    actor, lease, payable = (
        payout.batch.approved_by,
        payout.lease,
        payout.payables.get(),
    )
    instruction.delete()
    payout.payables.clear()
    payout.delete()
    payable.payout_status = "ready"
    payable.save()
    OwnerPaymentProfile.objects.filter(owner=lease.owner).update(
        accepted_policy_versions=["rental-policy-v1"]
    )
    RentalHandover.objects.create(
        lease=lease,
        kind="move_in",
        possession_on=lease.start_date,
        status="accepted",
        approvals=[str(lease.owner.id), str(lease.tenant.id)],
    )
    api = client_for(actor)
    preview = api.get(
        "/api/v1/features/v1/operations/payouts/preview/",
        {"payable_id": [str(payable.id)]},
    )
    assert preview.status_code == 200, preview.data
    data = {"request_key": str(uuid.uuid4()), "payable_ids": [str(payable.id)]}
    with patch(
        "core_apps.users.services.sensitive_actions.consume", wraps=consume
    ) as verify, patch.object(client, "transport") as network:
        created = api.post(
            "/api/v1/features/v1/operations/payouts/execute/", data, format="json"
        )
        assert created.status_code == 201, created.data
        again = api.post(
            "/api/v1/features/v1/operations/payouts/execute/", data, format="json"
        )
    assert created.data == again.data
    assert verify.call_count == 1
    assert verify.call_args.kwargs["payload"] == {
        "command": data,
        **preview.data["authorization_details"],
    }
    network.assert_not_called()
    item = PaymobPayout.objects.get()
    assert item.status == "queued"
    value = created.data["resource"]
    assert value["masked_beneficiary"] == "4050"
    assert value["submitted_at"] is None and value["succeeded_at"] is None
    assert [event["action"] for event in value["history"]] == ["approved"]


def test_old_owner_notice_stays_authorized_after_current_status_changes(instruction):
    from core_apps.features.planning_models import PlanningEvent
    from core_apps.features.services.payout_notifications import record, authorize

    with transaction.atomic():
        record(instruction.payout, "approved")
        record(instruction.payout, "approved")
    original = PlanningEvent.objects.get(destination__event_kind="payout_updated")
    with patch.object(client, "transport", side_effect=transport_for(instruction)):
        service.process(instruction)
    assert authorize(original)
    value = (
        client_for(original.recipient)
        .get(f"/api/v1/features/v1/payouts/{instruction.payout.id}/")
        .data
    )
    assert value["status"] == "paid"
    assert [row["action"] for row in value["history"]] == ["submitted", "paid"]
    assert "actor" not in str(value["history"])
    original.destination["lease_id"] = str(uuid.uuid4())
    with pytest.raises(NotFound):
        authorize(original)


def test_payout_notice_push_retry_checks_original_recipient(instruction):
    from core_apps.features.services.payout_notifications import record
    from core_apps.features.services.planning_notifications import (
        deliver_planning_events,
    )
    from core_apps.notifications.models import DeviceToken, PushDelivery
    from core_apps.notifications.services.push_delivery import dispatch

    DeviceToken.objects.create(
        user=instruction.payout.owner, token="synthetic-payout-token"
    )
    record(instruction.payout, "approved")
    assert deliver_planning_events(event_kinds=["payout_updated"]) == 1
    send_path = (
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device"
    )
    with patch(send_path, return_value=False):
        assert dispatch() == 0
    RentalPayout.objects.filter(pk=instruction.payout_id).update(
        owner=instruction.payout.lease.tenant
    )
    PushDelivery.objects.update(next_attempt_at=timezone.now() - timedelta(seconds=1))
    with patch(send_path) as send:
        assert dispatch() == 0
    send.assert_not_called()


@pytest.mark.parametrize(
    "role,allowed",
    [
        ("support", False),
        ("financial_approver", False),
        ("payout_operator", True),
        ("psp_reconciliation", True),
        ("security_recovery_reviewer", False),
    ],
)
def test_review_queue_keeps_payout_authority_separate(instruction, role, allowed):
    reviewer = User.objects.create_user(
        email=f"{role}-queue@example.com",
        password="pass",
        is_verified=True,
        is_superuser=role == "security_recovery_reviewer",
    )
    StaffProfile.objects.create(user=reviewer, role_name=role)
    for path in [
        "operations/payouts/",
        "operations/payables/",
        f"operations/payouts/{instruction.payout.id}/review/",
    ]:
        result = client_for(reviewer).get("/api/v1/features/v1/" + path)
        assert result.status_code == (200 if allowed else 403), result.data
    if role == "security_recovery_reviewer":
        result = client_for(reviewer).post(
            "/api/v1/features/v1/operations/payouts/execute/",
            {
                "payable_ids": [str(instruction.payout.payables.get().id)],
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        assert result.status_code == 403


def test_queue_has_real_counts_and_no_recipient_secrets(instruction):
    actor = instruction.payout.batch.approved_by
    result = client_for(actor).get("/api/v1/features/v1/operations/payouts/")
    assert result.status_code == 200 and result.data["count"] == 1
    assert result["Cache-Control"] == "private, no-store"
    assert result.data["results"][0]["resource"]["id"] == str(instruction.payout.id)
    assert "01020304050" not in json.dumps(result.data)


def test_confirmed_failure_retry_keeps_prior_attempt_and_requires_new_approval(
    instruction,
):
    from core_apps.users.services.sensitive_actions import consume

    failed = proof(instruction, disbursement_status="failed", status_code="500")
    with patch.object(
        client, "transport", side_effect=transport_for(instruction, submit=failed)
    ):
        service.process(instruction)
    payout = RentalPayout.objects.get(pk=instruction.payout_id)
    actor = payout.batch.approved_by
    path = f"/api/v1/features/v1/operations/payouts/{payout.id}/retry/"
    command = {"expected_revision": payout.revision, "request_key": str(uuid.uuid4())}
    with patch(
        "core_apps.users.services.sensitive_actions.consume",
        side_effect=PermissionDenied(),
    ):
        assert client_for(actor).post(path, command, format="json").status_code == 403
    assert PaymobPayout.objects.count() == 1
    with patch(
        "core_apps.users.services.sensitive_actions.consume", wraps=consume
    ) as verification:
        approved = client_for(actor).post(path, command, format="json")
        assert approved.status_code == 200, approved.data
        assert (
            client_for(actor).post(path, command, format="json").data == approved.data
        )
    assert verification.call_count == 1
    assert verification.call_args.kwargs["payload"]["approval_kind"] == "retry"
    replacement = PaymobPayout.objects.get(current=True)
    instruction.refresh_from_db()
    assert replacement.retry_of_id == instruction.pk
    assert replacement.reference != instruction.reference
    assert not instruction.current and instruction.status == "failed"
    assert instruction.provider_transaction_id == failed["transaction_id"]
    with patch.object(client, "transport") as network:
        service.process(instruction)
    network.assert_not_called()
    with patch.object(client, "transport", side_effect=transport_for(replacement)):
        assert service.process(replacement).status == "paid"
    assert PaymobPayout.objects.count() == 2
    assert (
        LedgerTransaction.objects.filter(reference=f"payout:{payout.id}").count() == 1
    )
    assert RentalOperationalCase.objects.filter(payout=payout).count() == 1
    review = client_for(actor).get(
        f"/api/v1/features/v1/operations/payouts/{payout.id}/review/"
    )
    assert [value["status"] for value in review.data["attempts"]] == [
        "failed",
        "confirmed",
    ]
    assert review.data["attempts"][1]["retry_of"] == str(instruction.id)


@pytest.mark.parametrize(
    "state", ["queued", "unknown", "processing", "submitting", "confirmed"]
)
def test_only_confirmed_failure_permits_a_new_attempt(instruction, state):
    instruction.status = state
    instruction.provider_transaction_id = str(uuid.uuid4())
    instruction.save()
    payout = instruction.payout
    result = client_for(payout.batch.approved_by).post(
        f"/api/v1/features/v1/operations/payouts/{payout.id}/retry/",
        {"expected_revision": payout.revision, "request_key": str(uuid.uuid4())},
        format="json",
    )
    assert result.status_code == 409
    assert PaymobPayout.objects.count() == 1


def test_concurrent_retry_approvals_create_only_one_current_attempt(instruction):
    with patch.object(
        client,
        "transport",
        side_effect=transport_for(
            instruction,
            submit=proof(instruction, disbursement_status="failed", status_code="500"),
        ),
    ):
        service.process(instruction)
    payout = RentalPayout.objects.get(pk=instruction.payout_id)

    def approve():
        close_old_connections()
        try:
            actor = User.objects.get(pk=payout.batch.approved_by_id)
            return (
                client_for(actor)
                .post(
                    f"/api/v1/features/v1/operations/payouts/{payout.id}/retry/",
                    {
                        "expected_revision": payout.revision,
                        "request_key": str(uuid.uuid4()),
                    },
                    format="json",
                )
                .status_code
            )
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: approve(), range(2))) == [200, 409]
    assert PaymobPayout.objects.filter(current=True).count() == 1
    assert PaymobPayout.objects.count() == 2


def test_pending_refund_hold_requires_resolution_and_new_approval(instruction):
    payout = instruction.payout
    payable = payout.payables.get()
    refund = RefundRequest.objects.create(
        lease=payout.lease,
        payment_attempt=payable.payment_attempt,
        requester=payout.lease.tenant,
        request_key=uuid.uuid4(),
        amount_minor=1000,
        refundable_balance_snapshot_minor=12345,
        allocations={"rent": 1000, "deposit": 0},
        status="requested",
    )
    assert service.claim(instruction.pk) is None
    instruction.refresh_from_db()
    payout.refresh_from_db()
    assert instruction.status == "held" and instruction.failure_code == "refund_pending"
    api = client_for(payout.batch.approved_by)
    base = f"/api/v1/features/v1/operations/payouts/{payout.id}/"
    review = api.get(base + "review/")
    assert review.status_code == 200 and review.data["can_reauthorize"]
    assert "reauthorize" not in review.data["allowed_actions"]
    body = {"request_key": str(uuid.uuid4()), "expected_revision": payout.revision}
    assert api.post(base + "reauthorize/", body, format="json").status_code == 409
    refund.status = "rejected"
    refund.save()
    details = api.get(base + "review/").data["authorization_details"]
    with patch(
        "core_apps.users.services.sensitive_actions.consume"
    ) as consume, patch.object(client, "transport") as send:
        result = api.post(base + "reauthorize/", body, format="json")
        assert result.status_code == 200, result.data
    send.assert_not_called()
    assert consume.call_args.kwargs["payload"] == {
        "command": body,
        "approval_kind": "reauthorize",
        **details,
    }
    instruction.refresh_from_db()
    assert instruction.status == "queued" and instruction.submitted_at is None
    with patch.object(client, "transport", side_effect=transport_for(instruction)):
        assert service.process(instruction).status == "paid"
    assert (
        LedgerTransaction.objects.filter(reference=f"payout:{payout.id}").count() == 1
    )


def test_review_of_same_recipient_can_accept_new_profile_revision(
    instruction, configured
):
    profile = OwnerPaymentProfile.objects.get(owner=instruction.payout.owner)
    previous_revision = profile.revision
    profile.revision += 1
    profile.save()
    configured.PAYMOB_PAYOUTS_BENEFICIARIES[profile.provider_account_id][
        "profile_revision"
    ] = profile.revision
    assert service.claim(instruction.pk) is None
    instruction.refresh_from_db()
    instruction.payout.refresh_from_db()
    assert instruction.failure_code == "beneficiary_changed"
    api = client_for(instruction.payout.batch.approved_by)
    base = f"/api/v1/features/v1/operations/payouts/{instruction.payout.id}/"
    review = api.get(base + "review/")
    assert "reauthorize" in review.data["allowed_actions"]
    assert (
        review.data["authorization_details"]["beneficiary_revision"] == profile.revision
    )
    body = {
        "request_key": str(uuid.uuid4()),
        "expected_revision": instruction.payout.revision,
    }
    with patch(
        "core_apps.users.services.sensitive_actions.consume",
        side_effect=PermissionDenied(),
    ):
        assert api.post(base + "reauthorize/", body, format="json").status_code == 403
    instruction.payout.refresh_from_db()
    assert instruction.payout.beneficiary_profile_revision == previous_revision
    with patch("core_apps.users.services.sensitive_actions.consume"), patch.object(
        client, "transport"
    ) as send:
        result = api.post(base + "reauthorize/", body, format="json")
        assert result.status_code == 200, result.data
        assert api.post(base + "reauthorize/", body, format="json").data == result.data
    send.assert_not_called()
    instruction.payout.refresh_from_db()
    assert instruction.payout.beneficiary_profile_revision == profile.revision
    assert PaymobPayout.objects.filter(payout=instruction.payout).count() == 1


def test_changed_recipient_cannot_be_accepted_as_renewed_approval(
    instruction, configured
):
    profile = OwnerPaymentProfile.objects.get(owner=instruction.payout.owner)
    profile.revision += 1
    profile.masked_beneficiary = {"account_last4": "4051"}
    profile.save()
    record = configured.PAYMOB_PAYOUTS_BENEFICIARIES[profile.provider_account_id]
    record.update(profile_revision=profile.revision, msisdn="01020304051")
    assert service.claim(instruction.pk) is None
    instruction.refresh_from_db()
    instruction.payout.refresh_from_db()
    api = client_for(instruction.payout.batch.approved_by)
    base = f"/api/v1/features/v1/operations/payouts/{instruction.payout.id}/"
    review = api.get(base + "review/")
    assert (
        review.data["can_reauthorize"]
        and "reauthorize" not in review.data["allowed_actions"]
    )
    with patch("core_apps.users.services.sensitive_actions.consume") as consume:
        response = api.post(
            base + "reauthorize/",
            {
                "request_key": str(uuid.uuid4()),
                "expected_revision": instruction.payout.revision,
            },
            format="json",
        )
    assert response.status_code == 409
    consume.assert_not_called()
    instruction.refresh_from_db()
    assert (
        instruction.status == "held"
        and targets.unseal(instruction)["msisdn"] == "01020304050"
    )


def test_unsettled_funding_must_be_restored_before_renewed_approval(instruction):
    payout = instruction.payout
    payable = payout.payables.get()
    attempt = payable.payment_attempt
    attempt.settlement_status = "pending"
    attempt.save(update_fields=["settlement_status"])
    assert service.claim(instruction.pk) is None
    instruction.refresh_from_db()
    payout.refresh_from_db()
    assert (
        instruction.failure_code == "payout_held" and instruction.submitted_at is None
    )
    api = client_for(payout.batch.approved_by)
    base = f"/api/v1/features/v1/operations/payouts/{payout.id}/"
    body = {"request_key": str(uuid.uuid4()), "expected_revision": payout.revision}
    assert "reauthorize" not in api.get(base + "review/").data["allowed_actions"]
    with patch("core_apps.users.services.sensitive_actions.consume") as consume:
        assert api.post(base + "reauthorize/", body, format="json").status_code == 409
    consume.assert_not_called()
    attempt.settlement_status = "settled"
    attempt.save(update_fields=["settlement_status"])
    assert "reauthorize" in api.get(base + "review/").data["allowed_actions"]
    with patch(
        "core_apps.users.services.sensitive_actions.consume"
    ) as consume, patch.object(client, "transport") as send:
        assert api.post(base + "reauthorize/", body, format="json").status_code == 200
    send.assert_not_called()
    assert len(consume.call_args.kwargs["payload"]["funding_digest"]) == 64
    instruction.refresh_from_db()
    assert instruction.status == "queued" and instruction.submitted_at is None
