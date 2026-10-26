"""Durable fault-injectable mock transport over canonical provider instructions.

Unknown results must be looked up before a new instruction may be issued. The
persisted mock outcome acts as the test provider's lookup ledger, not app success.
"""

from uuid import uuid5, NAMESPACE_URL
from rest_framework.exceptions import ValidationError
from ...models import RentalProviderInstruction
from ..rental_phase2 import fingerprint, RentalConflict
from .plans import record_step

BEHAVIORS = {"confirmed", "failed", "unknown_before", "unknown_after"}


def mock_instruction(
    plan, leg, *, kind, actor, request_key, behavior="confirmed", perform=None
):
    from config.advanced_housing import require_mock_mode

    require_mock_mode()
    if plan.provider_mode != "mock":
        raise ValidationError("This execution does not accept simulated provider outcomes.")
    if behavior not in BEHAVIORS or len(kind) > 21:
        raise ValidationError("Choose a supported mock provider outcome.")
    identity = str(
        uuid5(
            NAMESPACE_URL,
            f"advanced:{plan.id}:{leg.id}:{kind}:{actor.id}:{request_key}",
        )
    )
    reference = f"advanced:{identity}"
    payload = {
        "plan": plan.digest,
        "leg": str(leg.id),
        "kind": kind,
        "actor": str(actor.id),
        "behavior": behavior,
    }
    instruction = RentalProviderInstruction.objects.filter(reference=reference).first()
    if instruction:
        if instruction.request_fingerprint != fingerprint(payload):
            raise RentalConflict(
                "The original provider instruction has different inputs.",
                code="idempotency_conflict",
            )
        return instruction
    if RentalProviderInstruction.objects.filter(
        subject_id=leg.id, status="unknown"
    ).exists():
        raise RentalConflict(
            "Reconcile the original uncertain provider instruction first.",
            code="reconciliation_required",
        )
    instruction = RentalProviderInstruction.objects.create(
        reference=reference,
        kind=f"advanced_{kind}",
        provider="fake",
        subject_id=leg.id,
        subject_revision=plan.revision,
        request_fingerprint=fingerprint(payload),
        attempts=1,
    )
    result = {
        "provider_mode": "mock",
        "actor_id": str(actor.id),
        "mock_outcome": "not_applied",
    }
    if behavior in {"confirmed", "unknown_after"}:
        result.update(perform(instruction) if perform else {})
        result["mock_outcome"] = "applied"
    instruction.result = result
    instruction.status = (
        "unknown"
        if behavior.startswith("unknown")
        else ("confirmed" if behavior == "confirmed" else "failed")
    )
    instruction.provider_reference = f"mock-advanced:{identity}"
    instruction.failure_code = (
        "provider_timeout"
        if instruction.status == "unknown"
        else ("mock_rejected" if instruction.status == "failed" else "")
    )
    instruction.save()
    record_step(
        plan,
        leg,
        kind,
        instruction.status,
        "rental_provider_instruction",
        instruction.id,
        {"provider_mode": "mock"},
        actor=actor,
    )
    return instruction


def reconcile_instructions(plan, leg, actor):
    from config.advanced_housing import require_mock_mode

    require_mock_mode()
    for item in RentalProviderInstruction.objects.select_for_update().filter(
        subject_id=leg.id, status="unknown", provider="fake"
    ):
        # This is an original-reference lookup. It does not submit again.
        item.status = (
            "confirmed" if item.result.get("mock_outcome") == "applied" else "failed"
        )
        item.failure_code = "" if item.status == "confirmed" else "mock_not_applied"
        item.save(update_fields=["status", "failure_code", "updated_at"])
        record_step(
            plan,
            leg,
            "reconciliation",
            item.status,
            "rental_provider_instruction",
            item.id,
            {"provider_mode": "mock", "resubmitted": False},
            actor=actor,
        )
