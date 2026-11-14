"""Financial commands preserve original locks, receipts, authority and provider boundaries."""

from rest_framework import status
from core_apps.features.models import Lease, PayoutBatch, RentalPayout
from core_apps.features.services.payable_eligibility import evaluate_owner_payables
from django.utils import timezone
from core_apps.features.services.rental_phase3 import post_ledger_transaction
from .money_result import MoneyResult
from .money_projection import payout_payload
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from core_apps.features.models import (
    OwnerPayable,
    OwnerPaymentProfile,
    PaymobPayout,
    PayoutAuditEvent,
)
from core_apps.features.services import (
    paymob_payout_client as client,
    paymob_payout_targets as targets,
    paymob_payouts,
)
from core_apps.features.services.rental_phase2 import (
    RentalConflict,
    fingerprint,
    replay_operation,
    remember_mutation,
)
from core_apps.features.services.rental_lifecycle.provider_instructions import (
    validate_payout_instruction,
)
from .money_projection import _details
from .payout_authority import _require_payout_role


def approve_payout(actor, claims, data, proof):
    _require_payout_role(actor)
    payable_ids = data.get("payable_ids", [])
    request_key = data.get("request_key")
    if (
        not isinstance(payable_ids, list)
        or not payable_ids
        or any((not isinstance(x, str) for x in payable_ids))
        or (not request_key)
    ):
        raise ValidationError("payable_ids and request_key are required.")
    operation = "payout.execute"
    replay = replay_operation(actor, operation, request_key, data)
    if replay:
        return MoneyResult(replay[0], status=replay[1])
    with transaction.atomic():
        _require_payout_role(actor, lock=True)
        replay = replay_operation(actor, operation, request_key, data)
        if replay:
            return MoneyResult(replay[0], status=replay[1])
        lease_ids = list(
            OwnerPayable.objects.filter(id__in=payable_ids)
            .values_list("lease_id", flat=True)
            .order_by()
            .distinct()
        )
        if len(lease_ids) != 1:
            raise ValidationError("A payout batch must target one lease.")
        from ..services.rental_lifecycle.locks import lock_financial_lease

        lease = lock_financial_lease(Lease.objects.get(pk=lease_ids[0]))
        evaluate_owner_payables(lease)
        payables = list(
            OwnerPayable.objects.select_for_update(of=("self",))
            .select_related("lease__owner")
            .filter(id__in=payable_ids)
        )
        if len(payables) != len(set(payable_ids)) or any(
            (x.payout_status != "ready" for x in payables)
        ):
            raise RentalConflict(
                "Every payable must be eligible and unallocated.", code="payout_held"
            )
        if (
            len({x.invoice.beneficiary_id or x.lease.owner_id for x in payables}) != 1
            or len({x.lease_id for x in payables}) != 1
        ):
            raise ValidationError("A payout batch must target one owner and lease.")
        batch = PayoutBatch.objects.create(approved_by=actor, request_key=request_key)
        profile = OwnerPaymentProfile.objects.select_for_update().get(
            owner=payables[0].invoice.beneficiary or payables[0].lease.owner
        )
        if (
            not profile.payout_ready
            or profile.status != "ready"
            or (not profile.provider_account_id)
        ):
            raise RentalConflict(
                "The reviewed beneficiary is not ready.", code="payout_held"
            )
        recipient = None
        if profile.provider == "paymob_payouts":
            from ..services.paymob_payout_targets import for_profile

            recipient = for_profile(profile)
        from core_apps.users.services.sensitive_actions import consume_for_actor

        consume_for_actor(
            actor,
            claims,
            proof,
            action="payout.execute",
            resource_id=lease.id,
            revision=lease.revision,
            payload={
                "command": data,
                "amount_minor": sum((x.net_minor for x in payables)),
                "currency": "EGP",
                "beneficiary_revision": profile.revision,
                "beneficiary_account_digest": fingerprint(profile.provider_account_id),
                **({"recipient_digest": fingerprint(recipient)} if recipient else {}),
            },
        )
        payout = RentalPayout.objects.create(
            batch=batch,
            owner=payables[0].invoice.beneficiary or payables[0].lease.owner,
            lease=payables[0].lease,
            amount_minor=sum((x.net_minor for x in payables)),
            masked_beneficiary=profile.masked_beneficiary,
            beneficiary_profile_revision=profile.revision,
            beneficiary_provider=profile.provider,
            beneficiary_account_id=profile.provider_account_id,
        )
        payout.payables.set(payables)
        for payable in payables:
            payable.payout_status = "submitted"
            payable.revision += 1
            payable.save(update_fields=["payout_status", "revision", "updated_at"])
        PayoutAuditEvent.objects.create(payout=payout, actor=actor, action="approved")
        if recipient:
            from ..services.paymob_payouts import stage

            stage(payout, recipient)
        from ..services.payout_notifications import record

        record(payout, "approved")
        output = remember_mutation(
            user=actor,
            operation=operation,
            request_key=request_key,
            payload=data,
            request_subject_id=payables[0].lease.id,
            result_subject_id=payout.id,
            result_revision=payout.revision,
            resource=payout_payload(payout),
            response_status=201,
        )
    return MoneyResult(output, status=status.HTTP_201_CREATED)


def reconcile_payout(actor, claims, data, proof, payout_id):
    from .payout_authority import _reader

    instruction = PaymobPayout.objects.filter(
        payout__id=payout_id, current=True
    ).first()
    if instruction:
        _reader(actor)
    else:
        _require_payout_role(actor)
    request_key = data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"payout.reconcile.{payout_id}"
    replay = replay_operation(actor, operation, request_key, data)
    if replay:
        return MoneyResult(replay[0], status=replay[1])
    if instruction:
        from ..services.paymob_payouts import process

        process(instruction, allow_submit=False)
    with transaction.atomic():
        if instruction:
            _reader(actor)
        else:
            _require_payout_role(actor, lock=True)
        candidate = get_object_or_404(RentalPayout, id=payout_id)
        from ..services.rental_lifecycle.locks import lock_financial_lease

        lock_financial_lease(Lease.objects.get(pk=candidate.lease_id))
        replay = replay_operation(actor, operation, request_key, data)
        if replay:
            return MoneyResult(replay[0], status=replay[1])
        payout = get_object_or_404(
            RentalPayout.objects.select_for_update().prefetch_related("payables"),
            id=payout_id,
        )
        if payout.status != RentalPayout.Status.PAID and (not instruction):
            from ..services.rental_lifecycle.provider_instructions import (
                execute_local_instruction,
            )

            payout.provider_payout_id = execute_local_instruction(
                kind="payout",
                subject=payout,
                request_key=payout.batch.request_key,
                payload={
                    "amount_minor": payout.amount_minor,
                    "currency": payout.currency,
                    "beneficiary": payout.masked_beneficiary,
                },
            )
            payout.status = RentalPayout.Status.PAID
            payout.revision += 1
            payout.save()
            payout.payables.update(payout_status="succeeded", updated_at=timezone.now())
            post_ledger_transaction(
                reference=f"payout:{payout.id}",
                kind="owner_payout",
                lease=payout.lease,
                entries=[
                    ("owner_liability", "debit", payout.amount_minor),
                    ("platform_cash", "credit", payout.amount_minor),
                ],
            )
            PayoutAuditEvent.objects.create(
                payout=payout,
                actor=actor,
                action="paid",
                metadata={"provider_payout_id": payout.provider_payout_id},
            )
            from ..services.payout_notifications import record

            record(payout, "paid")
        output = remember_mutation(
            user=actor,
            operation=operation,
            request_key=request_key,
            payload=data,
            request_subject_id=payout.id,
            result_subject_id=payout.id,
            result_revision=payout.revision,
            resource=payout_payload(payout),
        )
    return MoneyResult(output)


def approve_again(actor, claims, data, proof, payout_id, *, retry=False):
    _require_payout_role(actor)
    key = data.get("request_key")
    import uuid

    try:
        uuid.UUID(str(key))
    except (ValueError, TypeError):
        raise ValidationError(
            {"request_key": "A UUID request key is required."}
        ) from None
    operation = f"payout.{('retry' if retry else 'reauthorize')}.{payout_id}"
    with transaction.atomic():
        actor = _require_payout_role(actor, lock=True)
        replay = replay_operation(actor, operation, key, data)
        if replay:
            return MoneyResult(replay[0], status=replay[1])
        candidate = get_object_or_404(PaymobPayout, payout__id=payout_id, current=True)
        item, payout, _ = paymob_payouts._locked(candidate.pk)
        if data.get("expected_revision") != payout.revision:
            raise RentalConflict(
                "Refresh the original payout review.", code="stale_revision"
            )
        if (
            retry
            and (item.status != "failed" or not item.provider_transaction_id)
            or (
                not retry
                and (
                    item.status != "held"
                    or item.failure_code not in UNSENT_REVIEW
                    or item.submitted_at is not None
                )
            )
        ):
            raise RentalConflict(
                "This instruction cannot be submitted again.",
                code="reconciliation_required",
            )
        profile = OwnerPaymentProfile.objects.select_for_update().get(
            owner=payout.owner
        )
        if (
            fingerprint(targets.for_profile(profile)) != item.recipient_digest
            or item.account_digest != client.account_digest()
        ):
            raise RentalConflict(
                "The original beneficiary changed.", code="beneficiary_changed"
            )
        if payout.amount_minor != item.amount_minor or payout.currency != item.currency:
            raise RentalConflict(
                "The original payout amount changed.", code="payout_changed"
            )
        validate_payout_instruction(
            payout, profile_revision=profile.revision if not retry else None
        )
        from core_apps.users.services.sensitive_actions import consume_for_actor

        consume_for_actor(
            actor,
            claims,
            proof,
            action="payout.execute",
            resource_id=payout.id,
            revision=payout.revision,
            payload={
                "command": data,
                "approval_kind": "retry" if retry else "reauthorize",
                **_details(item),
            },
        )
        if retry:
            previous = item
            previous.current = False
            previous.save(update_fields=["current", "updated_at"])
            item = paymob_payouts.stage(
                payout, targets.unseal(previous), actor=actor, retry_of=previous
            )
        else:
            item.authorization_context = paymob_payouts.authorization_context(actor)
            item.status, item.failure_code = ("queued", "")
            item.save(
                update_fields=[
                    "authorization_context",
                    "status",
                    "failure_code",
                    "updated_at",
                ]
            )
        payout.status = "created"
        previous_profile_revision = payout.beneficiary_profile_revision
        payout.beneficiary_profile_revision = profile.revision
        payout.failure_code = payout.hold_reason = ""
        payout.revision += 1
        payout.save()
        PayoutAuditEvent.objects.create(
            payout=payout,
            actor=actor,
            action="retry_approved" if retry else "reauthorized",
            metadata={
                "instruction_id": str(item.id),
                "previous_beneficiary_revision": previous_profile_revision,
                "beneficiary_revision": profile.revision,
                "funding_digest": _details(item)["funding_digest"],
            },
        )
        from core_apps.features.services.payout_notifications import record

        record(payout, "retry_approved" if retry else "reauthorized")
        result = remember_mutation(
            user=actor,
            operation=operation,
            request_key=key,
            payload=data,
            request_subject_id=payout.id,
            result_subject_id=payout.id,
            result_revision=payout.revision,
            resource=payout_payload(payout),
        )
    return MoneyResult(result)


UNSENT_REVIEW = {
    "authorization_changed",
    "beneficiary_changed",
    "payout_held",
    "refund_pending",
}

__all__ = ["approve_again", "approve_payout", "reconcile_payout"]
