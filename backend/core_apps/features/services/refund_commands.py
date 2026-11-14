"""Financial commands preserve original locks, receipts, authority and provider boundaries."""

from rest_framework import status
from rest_framework.exceptions import ValidationError
from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import Lease, PaymentAttempt
from core_apps.common.command_authority import recheck_actor_session
from core_apps.features.services.commands import money_minor
from core_apps.features.services.refunds import validate_allocations
from core_apps.features.services.rental_phase6 import refundable_balance_minor
from rest_framework.exceptions import NotFound
from core_apps.features.providers import fake_provider_available
from core_apps.features.services.rental_phase6 import evaluate_financial_closure
from .money_result import MoneyResult
from .money_access import personal_financial_lease, refund_for
from .money_projection import refund_payload
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from core_apps.features.models import RefundRequest, PaymobRefund
from core_apps.features.services import paymob_client, paymob_refunds
from core_apps.features.services.commands import command_identity
from core_apps.features.services.financial_authority import (
    require_financial_actor,
    authorization_context,
)
from core_apps.features.services.rental_lifecycle.locks import lock_financial_lease
from core_apps.features.services.rental_phase2 import (
    RentalConflict,
    replay_operation,
    remember_mutation,
)
from core_apps.features.services.money_projection import details as details


def request_refund(actor, claims, data, proof):
    from ..rental_serializers_parts.command_serializers import (
        RefundCreateCommand,
        validated,
    )
    from rest_framework.exceptions import NotFound
    from core_apps.common.command_fields import is_uuid

    body = data if hasattr(data, "get") else {}
    if not is_uuid(body.get("payment_attempt_id")):
        raise NotFound()
    attempt = get_object_or_404(
        PaymentAttempt.objects.select_related("invoice__lease").filter(
            payer=actor, invoice__lease__isnull=False, invoice__purpose="rent"
        ),
        id=body["payment_attempt_id"],
    )
    lease = personal_financial_lease(actor, attempt.invoice.lease.id, write=True)
    if actor != attempt.payer:
        raise PermissionDenied("Only the captured payer can request a refund.")
    request_key, expected_revision = command_identity(data)
    command = validated(RefundCreateCommand, data)
    if expected_revision != 0:
        raise ValidationError(
            {"expected_revision": "A new refund starts at revision 0."}
        )
    if command.get("lease_id") and str(command["lease_id"]) != str(lease.id):
        raise ValidationError({"lease_id": "Payment belongs to a different lease."})
    operation = f"refund.create.{attempt.id}"
    replay = replay_operation(actor, operation, request_key, data)
    if replay:
        return MoneyResult(replay[0], status=replay[1])
    amount = money_minor(data.get("amount"))
    if (
        not isinstance(amount, int)
        or amount <= 0
        or amount > refundable_balance_minor(attempt)
    ):
        raise RentalConflict(
            "Refund exceeds the remaining refundable capture balance.",
            code="refund_exceeds_balance",
        )
    with transaction.atomic():
        lease = personal_financial_lease(actor, lease.id, lock=True, write=True)
        attempt = PaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
        replay = replay_operation(actor, operation, request_key, data)
        if replay:
            return MoneyResult(replay[0], status=replay[1])
        recheck_actor_session(actor, claims)
        if amount > refundable_balance_minor(attempt):
            raise RentalConflict(
                "Refund exceeds the remaining refundable capture balance.",
                code="refund_exceeds_balance",
            )
        from ..services.chargebacks.funding import can_refund

        if not can_refund(attempt):
            raise RentalConflict(
                "Only confirmed captures can be refunded.", code="payment_not_captured"
            )
        if command.get("payment_revision", attempt.revision) != attempt.revision:
            raise RentalConflict("Payment revision conflict.", code="stale_revision")
        allocations = validate_allocations(attempt, amount, data.get("allocations"))
        item = RefundRequest.objects.create(
            lease=lease,
            payment_attempt=attempt,
            requester=actor,
            amount_minor=amount,
            refundable_balance_snapshot_minor=refundable_balance_minor(attempt),
            reason=command["reason"],
            request_key=request_key,
            allocations=allocations,
        )
        from ..services.refund_notifications import record

        record(item, "requested", actor)
        output = remember_mutation(
            user=actor,
            operation=operation,
            request_key=request_key,
            payload=data,
            request_subject_id=attempt.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=refund_payload(item),
            response_status=201,
        )
    return MoneyResult(output, status=status.HTTP_201_CREATED)


def respond_refund(actor, claims, data, proof, refund_id):
    from ..services.financial_authority import require_financial_actor
    from ..services.paymob_refunds import ROLES

    require_financial_actor(actor, ROLES, "refund.review")
    item = refund_for(actor, refund_id, allow_operations=True)
    from ..rental_serializers_parts.command_serializers import (
        RefundRespondCommand,
        validated,
    )

    data = data if hasattr(data, "get") else {}
    action = data.get("action") or data.get("decision")
    if not isinstance(action, str) or action not in {"approve", "reject"}:
        raise ValidationError({"action": "Must be approve or reject."})
    command = validated(RefundRespondCommand, data)
    request_key = command["request_key"]
    operation = f"refund.respond.{item.id}"
    with transaction.atomic():
        require_financial_actor(actor, ROLES, "refund.review", lock=True)
        from ..services.rental_lifecycle.locks import lock_financial_lease

        if item.purpose == "chargeback_excess":
            from ..services.chargebacks.operations import require_operator

            require_financial_actor(
                actor,
                {
                    StaffProfile.RoleName.REFUND_OPERATOR,
                    StaffProfile.RoleName.FINANCIAL_APPROVER,
                },
                "chargeback.approve_refund",
                lock=True,
            )
            require_operator(actor, item.lease, lock=True)
        lock_financial_lease(Lease.objects.get(pk=item.lease_id))
        item = refund_for(actor, refund_id, allow_operations=True, lock=True)
        if item.purpose == "chargeback_excess":
            require_operator(actor, item.lease, lock=True)
            if action != "approve":
                raise RentalConflict(
                    "Rejecting a review cannot erase evidenced excess funds; retain the refund for reconciliation."
                )
        replay = replay_operation(actor, operation, request_key, data)
        if replay:
            return MoneyResult(replay[0], status=replay[1])
        recheck_actor_session(actor, claims)
        if item.revision != command["expected_revision"]:
            raise RentalConflict("Refund revision conflict.", code="stale_revision")
        if item.status != RefundRequest.Status.REQUESTED:
            raise RentalConflict("Only a requested refund can be approved or rejected.")
        item.status = (
            RefundRequest.Status.APPROVED
            if action == "approve"
            else RefundRequest.Status.REJECTED
        )
        item.approved_by = actor
        item.revision += 1
        item.save()
        from ..services.refund_notifications import record

        record(item, "approved" if action == "approve" else "rejected", actor)
        output = remember_mutation(
            user=actor,
            operation=operation,
            request_key=request_key,
            payload=data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=refund_payload(item),
        )
    return MoneyResult(output)


def execute_refund_command(actor, claims, data, proof, refund_id):
    from ..services.refunds import execute_refund
    from ..services.rental_phase3 import post_ledger_transaction
    from ..services.financial_authority import require_financial_actor

    roles = {
        StaffProfile.RoleName.REFUND_OPERATOR,
        StaffProfile.RoleName.FINANCIAL_APPROVER,
    }
    require_financial_actor(actor, roles, "refund.execute")
    item = refund_for(actor, refund_id, allow_operations=True)
    key, revision = command_identity(data, minimum=1)
    recover = data.get("action") == "confirm_owner_recovery"
    if data.get("action", "execute") not in {"execute", "confirm_owner_recovery"}:
        raise ValidationError({"action": "Use execute or confirm_owner_recovery."})
    if recover and (not fake_provider_available()):
        raise NotFound()
    operation = f"refund.{('recover' if recover else 'execute')}.{item.id}"
    with transaction.atomic():
        require_financial_actor(actor, roles, "refund.execute", lock=True)
        from ..services.rental_lifecycle.locks import lock_financial_lease

        lease = lock_financial_lease(Lease.objects.get(pk=item.lease_id))
        item = RefundRequest.objects.select_for_update().get(pk=item.pk)
        if item.purpose == "chargeback_excess":
            from ..services.chargebacks.operations import require_operator

            require_operator(actor, lease, lock=True)
        replay = replay_operation(actor, operation, key, data)
        if replay:
            return MoneyResult(replay[0], status=replay[1])
        if item.revision != revision:
            raise RentalConflict("Refund revision conflict.", code="stale_revision")
        if recover:
            outstanding = item.owner_recovery_minor - item.owner_recovered_minor
            if item.status != "succeeded" or outstanding <= 0:
                raise RentalConflict("No owner recovery is outstanding.")
            if money_minor(data.get("amount")) != outstanding:
                raise ValidationError(
                    {"amount": "Confirm the exact outstanding owner recovery."}
                )
            post_ledger_transaction(
                reference=f"owner-recovered:{item.id}",
                kind="owner_recovery",
                lease=lease,
                entries=[
                    ("platform_cash", "debit", outstanding),
                    ("owner_receivable", "credit", outstanding),
                ],
                metadata={"provider_mode": "mock", "actor_id": str(actor.id)},
            )
            item.owner_recovered_minor += outstanding
            item.recovery_reference = f"mock-recovery:{key}"
            item.revision += 1
            item.save()
        else:
            if item.status != "approved":
                raise RentalConflict("Only an approved refund can execute.")
            from .money_projection import details
            from core_apps.users.services.sensitive_actions import consume_for_actor

            consume_for_actor(
                actor,
                claims,
                proof,
                action="refund.execute",
                resource_id=item.id,
                revision=item.revision,
                payload={"command": data, **details(item)},
            )
            item = execute_refund(item, actor=actor)
        evaluate_financial_closure(lease)
        return MoneyResult(
            remember_mutation(
                user=actor,
                operation=operation,
                request_key=key,
                payload=data,
                request_subject_id=item.id,
                result_subject_id=item.id,
                result_revision=item.revision,
                resource=refund_payload(item),
            )
        )


def retry_refund(actor, claims, data, proof, refund_id):
    key, revision = command_identity(data, minimum=1)
    operation = f"refund.retry.{refund_id}"
    with transaction.atomic():
        actor = require_financial_actor(
            actor, paymob_refunds.ROLES, operation, lock=True
        )
        replay = replay_operation(actor, operation, key, data)
        if replay:
            return MoneyResult(replay[0], status=replay[1])
    candidate = get_object_or_404(
        PaymobRefund.objects.select_related("refund__lease", "payment"),
        refund__id=refund_id,
        current=True,
    )
    if (
        str(candidate.id) != data.get("failed_instruction_id")
        or candidate.status != "failed"
        or candidate.refund.revision != revision
    ):
        with transaction.atomic():
            actor = require_financial_actor(
                actor, paymob_refunds.ROLES, operation, lock=True
            )
            replay = replay_operation(actor, operation, key, data)
            if replay:
                return MoneyResult(replay[0], status=replay[1])
        raise RentalConflict(
            "Refresh the failed attempt before retrying.", code="stale_revision"
        )
    if not paymob_client.refund_ready():
        raise paymob_client.PaymobUnavailable()
    paymob_refunds.verify_result(candidate)
    with transaction.atomic():
        actor = require_financial_actor(
            actor, paymob_refunds.ROLES, operation, lock=True
        )
        replay = replay_operation(actor, operation, key, data)
        if replay:
            return MoneyResult(replay[0], status=replay[1])
        lock_financial_lease(candidate.refund.lease)
        refund = RefundRequest.objects.select_for_update().get(pk=candidate.refund_id)
        item = PaymobRefund.objects.select_for_update().get(pk=candidate.pk)
        if refund.revision != revision or not item.current:
            raise RentalConflict("Refresh the original refund.", code="stale_revision")
        if (
            refund.status != "failed"
            or refund.failure_code != "provider_declined"
            or item.status != "failed"
            or (item.resolved_at is None)
            or (item.result_snapshot.get("success") is not False)
            or (item.result_snapshot.get("pending") is not False)
        ):
            raise RentalConflict(
                "Reconcile the original outcome before retrying.",
                code="reconciliation_required",
            )
        if (
            refund.payment_attempt_id != item.payment.attempt_id
            or refund.amount_minor != item.amount_minor
            or refund.allocations != item.allocations
        ):
            raise RentalConflict("The refund details changed.", code="invoice_changed")
        from core_apps.features.services.chargebacks.funding import can_refund
        from core_apps.features.services.refunds import validate_allocations

        if not can_refund(refund.payment_attempt):
            raise RentalConflict(
                "The original funding requires reconciliation.",
                code="payment_not_captured",
            )
        split = validate_allocations(
            refund.payment_attempt,
            item.amount_minor,
            item.allocations,
            exclude_refund=refund,
        )
        from core_apps.users.services.sensitive_actions import consume_for_actor

        consume_for_actor(
            actor,
            claims,
            proof,
            action="refund.execute",
            resource_id=refund.id,
            revision=refund.revision,
            payload={"command": data, "approval_kind": "retry", **details(refund)},
        )
        item.current = False
        item.save(update_fields=["current", "updated_at"])
        paymob_refunds.stage(
            refund, refund.payment_attempt, split, actor=actor, retry_of=item
        )
        return MoneyResult(
            remember_mutation(
                user=actor,
                operation=operation,
                request_key=key,
                payload=data,
                request_subject_id=refund.id,
                result_subject_id=refund.id,
                result_revision=refund.revision,
                resource=refund_payload(refund),
            )
        )


def reauthorize_refund(actor, claims, data, proof, refund_id):
    key, revision = command_identity(data, minimum=1)
    operation = f"refund.reauthorize.{refund_id}"
    with transaction.atomic():
        actor = require_financial_actor(
            actor, paymob_refunds.ROLES, operation, lock=True
        )
        replay = replay_operation(actor, operation, key, data)
        if replay:
            return MoneyResult(replay[0], status=replay[1])
        candidate = get_object_or_404(
            PaymobRefund.objects.select_related("refund__lease"),
            refund__id=refund_id,
            current=True,
        )
        lock_financial_lease(candidate.refund.lease)
        refund = RefundRequest.objects.select_for_update().get(pk=candidate.refund_id)
        item = PaymobRefund.objects.select_for_update().get(pk=candidate.pk)
        if refund.revision != revision:
            raise RentalConflict("Refresh the original refund.", code="stale_revision")
        if (
            item.status != "held"
            or item.failure_code != "authorization_changed"
            or item.submitted_at is not None
            or (refund.status != "processing")
        ):
            raise RentalConflict(
                "An unknown refund cannot be submitted again.",
                code="reconciliation_required",
            )
        if not paymob_client.refund_ready():
            raise paymob_client.PaymobUnavailable()
        if (
            refund.amount_minor != item.amount_minor
            or refund.allocations != item.allocations
        ):
            raise RentalConflict("The refund details changed.", code="invoice_changed")
        from core_apps.users.services.sensitive_actions import consume_for_actor

        consume_for_actor(
            actor,
            claims,
            proof,
            action="refund.execute",
            resource_id=refund.id,
            revision=refund.revision,
            payload={
                "command": data,
                "approval_kind": "reauthorize",
                **details(refund),
            },
        )
        item.authorization_context = authorization_context(actor)
        item.status, item.failure_code = ("queued", "")
        item.save(
            update_fields=[
                "authorization_context",
                "status",
                "failure_code",
                "updated_at",
            ]
        )
        refund.failure_code = ""
        refund.revision += 1
        refund.save(update_fields=["failure_code", "revision", "updated_at"])
        from core_apps.features.services.refund_notifications import record

        record(refund, "reauthorized", actor)
        return MoneyResult(
            remember_mutation(
                user=actor,
                operation=operation,
                request_key=key,
                payload=data,
                request_subject_id=refund.id,
                result_subject_id=refund.id,
                result_revision=refund.revision,
                resource=refund_payload(refund),
            )
        )


__all__ = [
    "details",
    "execute_refund_command",
    "reauthorize_refund",
    "request_refund",
    "respond_refund",
    "retry_refund",
]
