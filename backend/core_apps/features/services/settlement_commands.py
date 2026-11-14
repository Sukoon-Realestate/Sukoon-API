from core_apps.common.command_authority import recheck_actor_session
import uuid
from core_apps.features.models import RentalEvidence
from core_apps.features.services.commands import money_minor
from core_apps.features.services.settlements import (
    LINE_TYPES,
    financial_snapshot,
    prepare_settlement,
)
from django.db import transaction
from rest_framework.exceptions import ValidationError
from core_apps.features.models import FinalSettlement, RentalDocument
from core_apps.features.services.commands import command_identity
from core_apps.features.services.settlements import execute_settlement
from core_apps.features.services.settlement_notes import remember_note, validated_note
from core_apps.features.services.rental_phase2 import (
    RentalConflict,
    remember_mutation,
    replay_operation,
)
from core_apps.features.services.rental_phase6 import evaluate_financial_closure
from .money_access import personal_financial_lease
from .money_projection import _money
from .money_result import MoneyResult
from .settlement_projection import settlement_payload

"Final-settlement proposal/acceptance commands with original financial sources."


def propose_settlement(actor, claims, data, proof, lease_id):
    lease = personal_financial_lease(actor, lease_id, write=True)
    request_key, expected_revision = command_identity(data, minimum=1)
    operation = f"settlement.propose.{lease.id}"
    replay = replay_operation(actor, operation, request_key, data)
    if replay:
        return MoneyResult(replay[0], status=replay[1])
    note = validated_note(data)
    lines = []
    seen = set()
    if not isinstance(data.get("lines", []), list) or len(data.get("lines", [])) > 100:
        raise ValidationError({"lines": "Supply at most 100 settlement lines."})
    for raw in data.get("lines", []):
        if not isinstance(raw, dict):
            raise ValidationError({"lines": "Each line must be an object."})
        line_id = str(raw.get("id") or uuid.uuid4())
        amount = money_minor(raw.get("amount"), allow_negative=True)
        if (
            line_id in seen
            or raw.get("type") not in LINE_TYPES
            or (not isinstance(amount, int))
        ):
            raise ValidationError(
                {
                    "lines": "Each line needs a unique ID, supported type, and integer EGP amount."
                }
            )
        evidence_ids = raw.get("evidence_ids", [])
        if RentalEvidence.objects.filter(
            id__in=evidence_ids,
            lease=lease,
            malware_status=RentalEvidence.MalwareStatus.SAFE,
        ).count() != len(set(evidence_ids)):
            raise ValidationError(
                {"lines": "Line evidence must be safe and belong to this lease."}
            )
        seen.add(line_id)
        lines.append(
            {
                "id": line_id,
                "type": raw["type"],
                "label": raw.get("label", raw["type"]),
                "description": raw.get("description")
                or raw.get("label")
                or raw["type"],
                "amount": _money(amount),
                "evidence_ids": list(evidence_ids),
                **(
                    {
                        "maintenance_request_id": raw.get("maintenance_request_id"),
                        "cost_version": raw.get("cost_version"),
                    }
                    if raw["type"] == "maintenance"
                    else {}
                ),
                **(
                    {"invoice_id": str(raw["invoice_id"])}
                    if raw.get("invoice_id")
                    else {}
                ),
            }
        )
    with transaction.atomic():
        lease = personal_financial_lease(actor, lease_id, lock=True, write=True)
        recheck_actor_session(actor, claims)
        replay = replay_operation(actor, operation, request_key, data)
        if replay:
            return MoneyResult(replay[0], status=replay[1])
        item = _settlement(lease)
        if item.revision != expected_revision:
            raise RentalConflict("Settlement revision conflict.", code="stale_revision")
        if item.status == FinalSettlement.Status.ACCEPTED:
            raise RentalConflict("An accepted settlement cannot be rewritten.")
        plan = prepare_settlement(lease, lines)
        item.history.append(
            {
                "revision": item.revision,
                "status": item.status,
                "lines": item.lines,
                "accepted_by": item.accepted_by,
                "disputed_item_ids": item.disputed_item_ids,
            }
        )
        item.lines = lines
        item.financial_snapshot = financial_snapshot(lease)
        item.execution_plan = plan
        for field in (
            "rent_balance_minor",
            "deposit_to_return_minor",
            "refund_due_minor",
            "total_due_minor",
        ):
            setattr(item, field, plan[field])
        item.status = FinalSettlement.Status.PROPOSED
        item.accepted_by = [str(actor.id)]
        item.disputed_item_ids = []
        item.proposed_by = actor
        item.revision += 1
        remember_note(item, actor, "propose", note, request_key)
        item.save()
        output = remember_mutation(
            user=actor,
            operation=operation,
            request_key=request_key,
            payload=data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=settlement_payload(item, actor),
        )
    return MoneyResult(output)


def respond_settlement(actor, claims, data, proof, lease_id):
    lease = personal_financial_lease(actor, lease_id, write=True)
    request_key, expected_revision = command_identity(data, minimum=1)
    action = data.get("action") or data.get("decision")
    if action not in {"accept", "dispute"} or not data.get("request_key"):
        raise ValidationError("accept/dispute and request_key are required.")
    operation = f"settlement.respond.{lease.id}.{actor.id}"
    replay = replay_operation(actor, operation, data["request_key"], data)
    if replay:
        return MoneyResult(replay[0], status=replay[1])
    note = validated_note(data)
    with transaction.atomic():
        lease = personal_financial_lease(actor, lease_id, lock=True, write=True)
        recheck_actor_session(actor, claims)
        replay = replay_operation(actor, operation, request_key, data)
        if replay:
            return MoneyResult(replay[0], status=replay[1])
        item = FinalSettlement.objects.select_for_update().get(lease=lease)
        if item.revision != expected_revision:
            raise RentalConflict("Settlement revision conflict.", code="stale_revision")
        if item.status != FinalSettlement.Status.PROPOSED:
            raise RentalConflict("This settlement is not awaiting approval.")
        if str(actor.id) in item.accepted_by and action == "accept":
            raise RentalConflict("You already accepted this revision.")
        current_ids = {line["id"] for line in item.lines}
        if action == "dispute":
            disputed = set(map(str, data.get("item_ids", [])))
            if not disputed or not disputed.issubset(current_ids):
                raise ValidationError(
                    {"item_ids": "Choose persisted settlement item IDs."}
                )
            item.disputed_item_ids = sorted(disputed)
            item.status = FinalSettlement.Status.DISPUTED
            item.accepted_by = []
        else:
            accepted = set(item.accepted_by)
            accepted.add(str(actor.id))
            item.accepted_by = sorted(accepted)
            if {str(lease.owner.id), str(lease.tenant.id)}.issubset(accepted):
                item.status = FinalSettlement.Status.ACCEPTED
        item.revision += 1
        remember_note(item, actor, action, note, request_key)
        item.save()
        if item.status == FinalSettlement.Status.ACCEPTED:
            item = execute_settlement(item)
            RentalDocument.objects.get_or_create(
                lease=lease,
                document_type=RentalDocument.DocumentType.SETTLEMENT,
                title="Final settlement",
                defaults={"requested_by": actor},
            )
        evaluate_financial_closure(lease)
        output = remember_mutation(
            user=actor,
            operation=operation,
            request_key=data["request_key"],
            payload=data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=settlement_payload(item, actor),
        )
    return MoneyResult(output)


def _settlement(lease):
    item, _ = FinalSettlement.objects.get_or_create(lease=lease)
    return item


__all__ = ["propose_settlement", "respond_settlement"]
