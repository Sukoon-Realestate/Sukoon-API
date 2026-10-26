"""Sensitive refund dispatch and read-only provider recovery, with simulated HTTP."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import pytest
from django.db import close_old_connections
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.admin_api.models import StaffProfile
from core_apps.users.models import User, StaffSecurityIdentity, TotpRecoveryRequest
from core_apps.features.models import (
    PaymobRefund,
    RefundRequest,
    LedgerTransaction,
    RentalOperationalCase,
)
from core_apps.features.services import paymob_client, paymob_refunds
from core_apps.features.services.refunds import execute_refund
from core_apps.features.tests import test_paymob_invoice_payments as fixtures
from core_apps.users.tests import test_totp_recovery as assurance_fixtures

phase3_lease = fixtures.phase3_lease
paymob = fixtures.paymob
assurance_actors = assurance_fixtures.actors
pytestmark = pytest.mark.django_db(transaction=True)
ROOT = "/api/v1/features/v1/"


@pytest.fixture
def instruction(phase3_lease, paymob):
    paymob.PAYMOB_REFUNDS_ENABLED = True
    payment = fixtures.captured_payment(phase3_lease)
    return PaymobRefund.objects.get(refund=fixtures.approved_refund(payment))


def provider_source(item):
    return fixtures.snapshot(item.payment, refunded_amount_cents=0)


def post(item, suffix, data=None, actor=None):
    return fixtures.client_for(actor or item.refund.approved_by).post(
        ROOT + f"operations/refunds/{item.refund.id}/{suffix}/",
        data or {},
        format="json",
    )


def test_request_approval_alone_cannot_stage_provider_money(phase3_lease, paymob):
    payment = fixtures.captured_payment(phase3_lease)
    refund = RefundRequest.objects.create(
        lease=payment.attempt.invoice.lease,
        payment_attempt=payment.attempt,
        requester=payment.attempt.payer,
        request_key=uuid.uuid4(),
        amount_minor=10000,
        refundable_balance_snapshot_minor=payment.attempt.amount_minor,
        status="approved",
        allocations={"rent": 10000, "deposit": 0},
        reason="QA",
    )
    with patch.object(paymob_client, "submit_refund") as send:
        assert execute_refund(refund).status == "approved"
    assert not PaymobRefund.objects.exists()
    send.assert_not_called()


@pytest.mark.parametrize("change", ["role", "frozen", "recovered", "legacy"])
def test_unsent_refund_checks_current_actor_and_recovery_history(instruction, change):
    actor = instruction.refund.approved_by
    if change == "role":
        StaffProfile.objects.filter(user=actor).update(role_name="support")
    elif change == "frozen":
        User.objects.filter(pk=actor.pk).update(sensitive_actions_frozen=True)
    elif change == "legacy":
        instruction.authorization_context = {}
        instruction.save()
    else:
        identity = StaffSecurityIdentity.objects.create(
            user=actor,
            person_reference="refund-qa",
            evidence_reference="qa",
            known_channel_reference="qa",
        )
        TotpRecoveryRequest.objects.create(
            user=actor,
            identity=identity,
            person_reference=identity.person_reference,
            reason="Lost factor",
            active=False,
            status="completed",
        )
    with patch.object(
        paymob_client, "inquiry", return_value=provider_source(instruction)
    ), patch.object(paymob_client, "submit_refund") as send:
        paymob_refunds.process(instruction)
        paymob_refunds.process(instruction)
    send.assert_not_called()
    instruction.refresh_from_db()
    assert instruction.status == "held" and instruction.submitted_at is None
    assert instruction.failure_code == "authorization_changed"
    assert (
        RentalOperationalCase.objects.filter(
            source_key=f"paymob-refund:{instruction.id}"
        ).count()
        == 1
    )


def test_fresh_reauthorization_only_queues_original_unsent_instruction(instruction):
    instruction.status, instruction.failure_code = "held", "authorization_changed"
    instruction.save()
    refund = instruction.refund
    body = {"request_key": str(uuid.uuid4()), "expected_revision": refund.revision}
    with patch(
        "core_apps.users.services.sensitive_actions.consume",
        side_effect=PermissionDenied(),
    ):
        assert post(instruction, "reauthorize", body).status_code == 403
    with patch(
        "core_apps.users.services.sensitive_actions.consume"
    ) as verify, patch.object(paymob_client, "submit_refund") as send:
        response = post(instruction, "reauthorize", body)
        assert response.status_code == 200, response.data
        assert post(instruction, "reauthorize", body).data == response.data
    assert verify.call_count == 1
    assert verify.call_args.kwargs["payload"] == {
        "command": body,
        "approval_kind": "reauthorize",
        "amount_minor": refund.amount_minor,
        "payment_attempt_id": str(refund.payment_attempt.id),
        "currency": "EGP",
        "allocations": refund.allocations,
    }
    send.assert_not_called()
    instruction.refresh_from_db()
    assert instruction.status == "queued" and instruction.submitted_at is None


def test_unknown_cannot_reauthorize_but_frozen_actor_can_query(instruction):
    instruction.status = "unknown"
    instruction.submitted_at = timezone.now()
    instruction.save()
    body = {
        "request_key": str(uuid.uuid4()),
        "expected_revision": instruction.refund.revision,
    }
    assert post(instruction, "reauthorize", body).status_code == 409
    User.objects.filter(pk=instruction.refund.approved_by_id).update(
        sensitive_actions_frozen=True
    )
    with patch.object(
        paymob_client,
        "inquiry",
        return_value=fixtures.refund_proof(instruction.payment),
    ), patch.object(paymob_client, "submit_refund") as send:
        response = post(instruction, "reconcile", {"provider_transaction_id": "999"})
        assert response.status_code == 200, response.data
    send.assert_not_called()
    assert response.data["resource"]["status"] == "succeeded"
    assert LedgerTransaction.objects.filter(kind="refund").count() == 1


def test_unverified_candidate_cannot_replace_unknown_identity(instruction):
    instruction.status = "unknown"
    instruction.save()
    with patch.object(
        paymob_client,
        "inquiry",
        return_value=fixtures.refund_proof(
            instruction.payment, parent_transaction=99999
        ),
    ):
        assert (
            post(
                instruction, "reconcile", {"provider_transaction_id": "999"}
            ).status_code
            == 409
        )
    instruction.refresh_from_db()
    assert (
        instruction.provider_transaction_id is None and instruction.status == "unknown"
    )
    assert not LedgerTransaction.objects.filter(kind="refund").exists()


def test_reconcile_does_not_dispatch_a_queued_refund(instruction):
    with patch.object(paymob_client, "submit_refund") as send:
        response = post(instruction, "reconcile")
    assert response.status_code == 200
    send.assert_not_called()
    instruction.refresh_from_db()
    assert instruction.status == "queued"


@pytest.mark.parametrize(
    "role,allowed",
    [
        ("refund_operator", True),
        ("financial_approver", True),
        ("psp_reconciliation", True),
        ("support", False),
        ("payout_operator", False),
        ("security_recovery_reviewer", False),
    ],
)
def test_read_roles_and_independent_recovery_superuser(instruction, role, allowed):
    actor = User.objects.create_user(
        email=f"{role}@example.com",
        password="test",
        is_superuser=role == "security_recovery_reviewer",
        is_verified=True,
    )
    StaffProfile.objects.create(user=actor, role_name=role)
    response = fixtures.client_for(actor).get(ROOT + "operations/refunds/")
    assert response.status_code == (200 if allowed else 403)
    if role == "psp_reconciliation":
        assert not response.data["results"][0]["can_reauthorize"]


def test_same_command_concurrent_reauthorization_has_one_effect(instruction):
    instruction.status, instruction.failure_code = "held", "authorization_changed"
    instruction.save()
    identity = instruction.pk
    data = {
        "request_key": str(uuid.uuid4()),
        "expected_revision": instruction.refund.revision,
    }

    def run():
        close_old_connections()
        try:
            result = post(PaymobRefund.objects.get(pk=identity), "reauthorize", data)
            return result.status_code, result.data
        finally:
            close_old_connections()

    with patch(
        "core_apps.users.services.sensitive_actions.consume"
    ) as verify, ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: run(), range(2)))
    assert [code for code, _ in responses] == [200, 200]
    assert responses[0] == responses[1]
    assert verify.call_count == 1


def test_original_refund_history_and_notification_recheck_private_access(instruction):
    from core_apps.features.models import PrivateAccessRevocation
    from core_apps.features.planning_models import PlanningEvent
    from core_apps.features.services.refund_notifications import authorize
    from rest_framework.exceptions import NotFound

    notice = PlanningEvent.objects.get(
        recipient=instruction.refund.lease.tenant,
        destination__event_kind="refund_updated",
    )
    assert notice.destination["refund_id"] == str(instruction.refund.id)
    assert (
        "amount" not in notice.destination
        and "provider_reference" not in notice.destination
    )
    with patch.object(
        paymob_client,
        "inquiry",
        side_effect=[
            provider_source(instruction),
            fixtures.refund_proof(instruction.payment),
        ],
    ), patch.object(paymob_client, "submit_refund", return_value={"id": 999}):
        paymob_refunds.process(instruction)
    assert authorize(notice)
    api = fixtures.client_for(notice.recipient)
    path = ROOT + f"refund-requests/{instruction.refund.id}/"
    result = api.get(path)
    assert result.status_code == 200
    assert result.data["status"] == "succeeded"
    assert [entry["action"] for entry in result.data["history"]] == [
        "authorized",
        "submitted",
        "succeeded",
    ]
    assert all(set(row) == {"action", "occurred_at"} for row in result.data["history"])
    PrivateAccessRevocation.objects.create(
        user=notice.recipient,
        lease=instruction.refund.lease,
        reason="QA revoked access",
    )
    with pytest.raises(NotFound):
        authorize(notice)
    assert api.get(path).status_code == 404
    assert (
        api.get(ROOT + "refund-requests/", {"workspace": "tenant"}).data["results"]
        == []
    )


def test_refund_notification_uses_the_durable_device_queue(instruction):
    from datetime import timedelta
    from core_apps.features.models import PrivateAccessRevocation
    from core_apps.features.services.planning_notifications import (
        deliver_planning_events,
    )
    from core_apps.notifications.models import DeviceToken, PushDelivery
    from core_apps.notifications.services.push_delivery import dispatch

    tenant = instruction.refund.lease.tenant
    DeviceToken.objects.create(user=tenant, token="synthetic-refund-device")
    assert deliver_planning_events(event_kinds=["refund_updated"]) == 2
    path = "core_apps.notifications.services.fcm_service.FCMService.send_push_to_device"
    with patch(path, return_value=False):
        assert dispatch() == 0
    PrivateAccessRevocation.objects.create(
        user=tenant, lease=instruction.refund.lease, reason="QA revoke"
    )
    PushDelivery.objects.update(next_attempt_at=timezone.now() - timedelta(seconds=1))
    with patch(path) as send:
        assert dispatch() == 0
    send.assert_not_called()


def test_delayed_unknown_result_cannot_reopen_confirmed_refund(instruction):
    with patch.object(
        paymob_client,
        "inquiry",
        side_effect=[
            provider_source(instruction),
            fixtures.refund_proof(instruction.payment),
        ],
    ), patch.object(paymob_client, "submit_refund", return_value={"id": 999}):
        paymob_refunds.process(instruction)
    paymob_refunds.review(instruction, "outcome_unknown")
    instruction.refresh_from_db()
    instruction.refund.refresh_from_db()
    assert instruction.status == "confirmed" and not instruction.failure_code
    assert (
        instruction.refund.status == "succeeded" and not instruction.refund.failure_code
    )
    assert not RentalOperationalCase.objects.filter(
        source_key=f"paymob-refund:{instruction.id}"
    ).exists()


def fail_instruction(item):
    item.status = "processing"
    item.submitted_at = timezone.now()
    item.provider_transaction_id = "999"
    item.save()
    proof = fixtures.refund_proof(
        item.payment, success=False, pending=False, error_occured=True
    )
    with patch.object(paymob_client, "inquiry", return_value=proof):
        paymob_refunds.verify_result(item)
    item.refresh_from_db()
    item.refund.refresh_from_db()
    return proof


def retry_body(item):
    item.refund.refresh_from_db()
    return {
        "request_key": str(uuid.uuid4()),
        "expected_revision": item.refund.revision,
        "failed_instruction_id": str(item.id),
    }


def test_confirmed_failure_history_and_explicit_retry_once(instruction):
    proof = fail_instruction(instruction)
    assert instruction.status == instruction.refund.status == "failed"
    assert instruction.resolved_at and instruction.result_snapshot["success"] is False
    assert not LedgerTransaction.objects.filter(kind="refund").exists()
    body = retry_body(instruction)
    with patch.object(paymob_client, "submit_refund") as send:
        paymob_refunds.process(instruction)
        with patch.object(paymob_client, "inquiry", return_value=proof), patch(
            "core_apps.users.services.sensitive_actions.consume",
            side_effect=PermissionDenied(),
        ):
            assert post(instruction, "retry", body).status_code == 403
        assert PaymobRefund.objects.filter(refund=instruction.refund).count() == 1
        with patch.object(paymob_client, "inquiry", return_value=proof), patch(
            "core_apps.users.services.sensitive_actions.consume"
        ) as consume:
            response = post(instruction, "retry", body)
            assert response.status_code == 200, response.data
            assert post(instruction, "retry", body).data == response.data
        assert consume.call_count == 1
        assert consume.call_args.kwargs["payload"]["command"] == body
        assert consume.call_args.kwargs["payload"]["approval_kind"] == "retry"
    send.assert_not_called()
    instruction.refresh_from_db()
    assert not instruction.current and instruction.status == "failed"
    replacement = PaymobRefund.objects.get(refund=instruction.refund, current=True)
    assert replacement.retry_of == instruction and replacement.status == "queued"
    assert replacement.amount_minor == instruction.amount_minor
    resource = response.data["resource"]
    assert [row["status"] for row in resource["attempts"]] == ["failed", "queued"]
    assert [row["action"] for row in resource["history"]][-2:] == ["failed", "retried"]
    assert "result_snapshot" not in str(
        resource
    ) and "authorization_context" not in str(resource)
    with patch.object(
        paymob_client,
        "inquiry",
        side_effect=[
            provider_source(replacement),
            fixtures.refund_proof(replacement.payment, id=1000),
        ],
    ), patch.object(paymob_client, "submit_refund", return_value={"id": 1000}) as send:
        paymob_refunds.process(replacement)
        paymob_refunds.process(replacement)
    assert send.call_count == 1
    assert LedgerTransaction.objects.filter(kind="refund").count() == 1
    instruction.refresh_from_db()
    assert instruction.status == "failed"


@pytest.mark.parametrize(
    "flags",
    [
        {"success": False, "pending": True, "error_occured": True},
        {"success": "false", "pending": False, "error_occured": True},
        {"success": False, "pending": "false", "error_occured": True},
        {"success": False, "pending": False, "error_occured": None},
    ],
)
def test_ambiguous_provider_flags_never_enable_retry(instruction, flags):
    instruction.status, instruction.provider_transaction_id = "unknown", "999"
    instruction.save()
    with patch.object(
        paymob_client,
        "inquiry",
        return_value=fixtures.refund_proof(instruction.payment, **flags),
    ):
        paymob_refunds.verify_result(instruction)
    instruction.refresh_from_db()
    assert instruction.status == "processing" and instruction.resolved_at is None
    assert post(instruction, "retry", retry_body(instruction)).status_code == 409
    assert not LedgerTransaction.objects.filter(kind="refund").exists()


def test_retry_rechecks_original_funding_and_role(instruction):
    proof = fail_instruction(instruction)
    body = retry_body(instruction)
    with patch.object(paymob_client, "inquiry", return_value=proof), patch(
        "core_apps.features.services.chargebacks.funding.can_refund", return_value=False
    ), patch("core_apps.users.services.sensitive_actions.consume") as consume:
        assert post(instruction, "retry", body).status_code == 409
    consume.assert_not_called()
    StaffProfile.objects.filter(user=instruction.refund.approved_by).update(
        role_name="support"
    )
    assert post(instruction, "retry", body).status_code == 403
    assert PaymobRefund.objects.filter(refund=instruction.refund).count() == 1


def test_changed_old_outcome_holds_unsent_retry_without_accounting(instruction):
    proof = fail_instruction(instruction)
    with patch.object(paymob_client, "inquiry", return_value=proof), patch(
        "core_apps.users.services.sensitive_actions.consume"
    ):
        assert post(instruction, "retry", retry_body(instruction)).status_code == 200
    replacement = PaymobRefund.objects.get(refund=instruction.refund, current=True)
    from core_apps.features.services.rental_phase2 import RentalConflict

    with patch.object(
        paymob_client,
        "inquiry",
        return_value=fixtures.refund_proof(instruction.payment),
    ), pytest.raises(RentalConflict):
        paymob_refunds.verify_result(instruction)
    replacement.refresh_from_db()
    assert (
        replacement.status == "held"
        and replacement.failure_code == "previous_outcome_changed"
    )
    with patch.object(paymob_client, "submit_refund") as send:
        paymob_refunds.process(replacement)
    send.assert_not_called()
    assert not LedgerTransaction.objects.filter(kind="refund").exists()


def test_concurrent_retries_have_one_new_attempt(instruction):
    proof = fail_instruction(instruction)
    identity, body = instruction.pk, retry_body(instruction)

    def run():
        close_old_connections()
        try:
            response = post(PaymobRefund.objects.get(pk=identity), "retry", body)
            return response.status_code, response.data
        finally:
            close_old_connections()

    with patch.object(paymob_client, "inquiry", return_value=proof), patch(
        "core_apps.users.services.sensitive_actions.consume"
    ) as consume, ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: run(), range(2)))
    assert [code for code, _ in responses] == [200, 200]
    assert responses[0] == responses[1]
    assert consume.call_count == 1
    assert PaymobRefund.objects.filter(refund=instruction.refund).count() == 2
    assert (
        PaymobRefund.objects.filter(refund=instruction.refund, current=True).count()
        == 1
    )


@pytest.mark.parametrize("expired", [False, True])
def test_retry_uses_real_single_use_totp_bound_to_failed_attempt(
    instruction, assurance_actors, expired
):
    from datetime import timedelta
    from core_apps.users.models import TotpFactor, SensitiveAuthorization
    from core_apps.users.services import totp, sensitive_actions
    from core_apps.users.tests.test_totp_recovery import request as security_request
    from core_apps.features.refund_operations import details
    from rest_framework.test import APIClient

    proof = fail_instruction(instruction)
    actor = instruction.refund.approved_by
    factor = TotpFactor.objects.create(
        user=actor,
        secret_ciphertext=totp.seal(totp.new_secret()),
        confirmed_at=timezone.now(),
    )
    session = security_request(actor)
    body = retry_body(instruction)
    challenge = sensitive_actions.begin(
        session,
        {
            "action": "refund.execute",
            "resource_id": str(instruction.refund.id),
            "resource_revision": instruction.refund.revision,
            "payload": {
                "command": body,
                "approval_kind": "retry",
                **details(instruction.refund),
            },
        },
    )
    code = totp.code_at(
        totp.unseal(factor.secret_ciphertext), int(timezone.now().timestamp()) // 30
    )
    permission = sensitive_actions.verify(session, challenge["id"], code)
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {session.auth}",
        HTTP_X_SOKOUN_AUTHORIZATION=permission["proof"],
    )
    url = ROOT + f"operations/refunds/{instruction.refund.id}/retry/"
    if expired:
        SensitiveAuthorization.objects.filter(id=challenge["id"]).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
    with patch.object(paymob_client, "inquiry", return_value=proof), patch.object(
        paymob_client, "submit_refund"
    ) as send:
        invalid = api.post(
            url, {**body, "failed_instruction_id": str(uuid.uuid4())}, format="json"
        )
        assert invalid.status_code == 409
        response = api.post(url, body, format="json")
        assert response.status_code == (403 if expired else 200), response.data
        if not expired:
            assert api.post(url, body, format="json").data == response.data
    send.assert_not_called()
    authorization = SensitiveAuthorization.objects.get(id=challenge["id"])
    assert bool(authorization.consumed_at) is not expired
    assert PaymobRefund.objects.filter(refund=instruction.refund).count() == (
        1 if expired else 2
    )
