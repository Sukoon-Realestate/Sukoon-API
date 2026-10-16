"""Durable provider identity and bounded recovery. No production adapter is enabled.

The current fake adapter is a pure deterministic function. Live transports must
be dispatched by a worker after the instruction transaction commits, and must
support lookup by the same reference before any unknown command is retried.
"""

from datetime import timedelta
from django.utils import timezone
from ...models import RentalProviderInstruction
from ...providers import fake_provider_available, get_rental_provider
from ..rental_phase2 import RentalConflict, fingerprint


def prepare_instruction(*, kind, subject, request_key, payload):
    reference = f"rental:{kind}:{subject.id}:{request_key}"
    digest = fingerprint(payload)
    item, _ = RentalProviderInstruction.objects.get_or_create(
        reference=reference,
        defaults={
            "kind": kind,
            "provider": "fake" if fake_provider_available() else "unconfigured",
            "subject_id": subject.id,
            "subject_revision": subject.revision,
            "request_fingerprint": digest,
        },
    )
    if item.request_fingerprint != digest:
        raise RentalConflict(
            "The provider instruction identity already has different inputs.",
            code="idempotency_conflict",
        )
    return item


def execute_local_instruction(*, kind, subject, request_key, payload):
    """Only the pure mock can run synchronously; this is never live money proof."""
    if not fake_provider_available():
        raise RentalConflict(
            "A production provider and reconciliation adapter are not configured.",
            code="capability_unavailable",
        )
    item = prepare_instruction(
        kind=kind, subject=subject, request_key=request_key, payload=payload
    )
    if item.status == "confirmed":
        return item.provider_reference
    if item.status == "unknown":
        raise RentalConflict(
            "Reconcile the original provider instruction.",
            code="reconciliation_required",
        )
    if kind == "payout":
        validate_payout_instruction(subject)
    provider = get_rental_provider()
    method = {"refund": provider.execute_refund, "payout": provider.execute_payout}.get(
        kind
    )
    if method is None:
        raise RentalConflict(
            "This instruction kind is not supported.", code="capability_unavailable"
        )
    reference = method(subject.id, request_key)
    item.provider_reference, item.status = reference, "confirmed"
    item.attempts += 1
    item.result = {"provider_mode": "mock", "reference": reference}
    item.save()
    return reference


def mark_unknown(item, *, code="provider_timeout"):
    """Recovery keeps its identity and never interprets a timeout as failure."""
    RentalProviderInstruction.objects.filter(pk=item.pk).exclude(
        status="confirmed"
    ).update(
        status="unknown",
        failure_code=code,
        next_attempt_at=timezone.now() + timedelta(minutes=2),
    )


def hold_payout_for_review(payout, error):
    """Keep its reserved obligation and open one accountable case, without retrying money."""
    from .cases import open_system_case

    code = str(error.get_codes())
    payout.status = "held"
    payout.failure_code = code
    payout.hold_reason = str(error.detail)[:255]
    payout.revision += 1
    payout.save()
    case = open_system_case(
        kind="beneficiary_issue" if code == "beneficiary_changed" else "payout_failure",
        source_key=f"payout-review:{payout.id}",
        lease=payout.lease,
        reason=payout.hold_reason,
        next_action="Review the original payout and reserved balance before any further instruction.",
    )
    if case.payout_id is None:
        case.payout = payout
        case.save(update_fields=["payout", "updated_at"])
    return payout


def validate_payout_instruction(payout):
    """Recheck before dispatch; a later profile edit cannot silently redirect funds."""
    from ...models import OwnerPaymentProfile, RefundRequest

    profile = (
        OwnerPaymentProfile.objects.select_for_update()
        .filter(owner=payout.owner)
        .first()
    )
    if (
        not profile
        or not profile.payout_ready
        or profile.status != "ready"
        or not payout.beneficiary_profile_revision
        or (
            profile.revision != payout.beneficiary_profile_revision
            or profile.provider_account_id != payout.beneficiary_account_id
            or profile.provider != payout.beneficiary_provider
        )
    ):
        raise RentalConflict(
            "Review the changed or restricted beneficiary before payout.",
            code="beneficiary_changed",
        )
    payables = list(
        payout.payables.select_for_update(of=("self",)).select_related(
            "payment_attempt"
        )
    )
    if (
        not payables
        or sum(value.net_minor for value in payables) != payout.amount_minor
        or any(
            value.payout_status not in {"submitted", "processing"}
            or (
                value.payment_attempt
                and (
                    value.payment_attempt.payment_status != "captured"
                    or value.payment_attempt.settlement_status != "settled"
                )
            )
            for value in payables
        )
    ):
        raise RentalConflict(
            "The reserved payout balance needs reconciliation.", code="payout_held"
        )
    if RefundRequest.objects.filter(
        payment_attempt_id__in=[value.payment_attempt_id for value in payables],
        status__in=["requested", "approved", "processing"],
    ).exists():
        raise RentalConflict(
            "A pending refund reserves this payment balance.", code="refund_pending"
        )
