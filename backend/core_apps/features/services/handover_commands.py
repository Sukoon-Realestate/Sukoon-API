"""Personal handover commands preserve account/root lock order and receipts."""

from .handover_reads import (
    lease_for,
    handover_for,
    handover_payload,
    _validate_evidence,
)
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from core_apps.features.models import Lease, RentalHandover
from core_apps.features.services.lease_permissions import handover_actions
from core_apps.features.services.rental_phase2 import (
    RentalConflict,
    remember_mutation,
    replay_operation,
)
from django.utils import timezone
from core_apps.features.services.rental_notes import (
    record_response_note,
    validated_note,
)
from core_apps.features.services.payable_eligibility import evaluate_owner_payables


def create_handover(actor, claims, command, receipt_data, lease, lease_id):
    operation = f"handover.create.{lease.id}.{command['kind']}"
    replay = replay_operation(actor, operation, command["request_key"], receipt_data)
    if replay:
        return (replay[0], replay[1])
    evidence = _validate_evidence(lease, command["evidence_ids"])
    with transaction.atomic():
        actor, lease = lease_for(actor, claims, lease_id, lock=True, write=True)
        if not actor.is_active or not actor.is_verified or lease.legacy_read_only:
            raise PermissionDenied(
                "A verified participant and a supported agreement are required."
            )
        if lease.status not in {
            Lease.Status.ACTIVE,
            Lease.Status.TERMINATION_PENDING,
            Lease.Status.ENDED,
        }:
            raise RentalConflict("Handover requires a paid active agreement.")
        if command["kind"] == "move_in" and lease.status != Lease.Status.ACTIVE:
            raise RentalConflict("Move-in requires an active agreement.")
        replay = replay_operation(
            actor, operation, command["request_key"], receipt_data
        )
        if replay:
            return (replay[0], replay[1])
        from core_apps.common.command_authority import recheck_actor_session

        recheck_actor_session(actor, claims)
        if lease.handovers.filter(kind=command["kind"]).exists():
            raise RentalConflict("This handover already exists.")
        handover = RentalHandover.objects.create(
            lease=lease,
            kind=command["kind"],
            status=RentalHandover.Status.PENDING_APPROVAL,
            possession_on=command["possession_on"],
            condition=command["condition"],
            keys=command["keys"],
            meters=command["meters"],
            inventory=command["inventory"],
        )
        handover.evidence.set(evidence)
        output = remember_mutation(
            user=actor,
            operation=operation,
            request_key=command["request_key"],
            payload=receipt_data,
            request_subject_id=lease.id,
            result_subject_id=handover.id,
            result_revision=handover.revision,
            resource=handover_payload(handover, actor),
            response_status=201,
        )
    return (output, status.HTTP_201_CREATED)


def update_handover(actor, claims, command, receipt_data, handover, handover_id):
    expected = command["expected_revision"]
    request_key = command["request_key"]
    operation = f"handover.update.{handover.id}"
    replay = replay_operation(actor, operation, request_key, receipt_data)
    if replay:
        return (replay[0], replay[1])
    with transaction.atomic():
        actor, handover = handover_for(
            actor, claims, handover_id, lock=True, write=True
        )
        replay = replay_operation(actor, operation, request_key, receipt_data)
        if replay:
            return (replay[0], replay[1])
        from core_apps.common.command_authority import recheck_actor_session

        recheck_actor_session(actor, claims)
        if handover.revision != expected:
            raise RentalConflict("Handover revision conflict.", code="stale_revision")
        if "edit_handover" not in handover_actions(actor, handover):
            raise RentalConflict("This handover cannot be edited.")
        evidence = _validate_evidence(handover.lease, command["evidence_ids"])
        for field in ("possession_on", "condition", "keys", "meters", "inventory"):
            if field in command:
                setattr(handover, field, command[field])
        handover.approvals = []
        handover.status = RentalHandover.Status.PENDING_APPROVAL
        handover.revision += 1
        handover.save()
        handover.evidence.set(evidence)
        output = remember_mutation(
            user=actor,
            operation=operation,
            request_key=request_key,
            payload=receipt_data,
            request_subject_id=handover.id,
            result_subject_id=handover.id,
            result_revision=handover.revision,
            resource=handover_payload(handover, actor),
        )
    return (output, 200)


def respond_handover(actor, claims, command, receipt_data, handover_id, action):
    actor, handover = handover_for(actor, claims, handover_id, write=True)
    operation = f"handover.respond.{handover.id}.{actor.id}"
    replay = replay_operation(actor, operation, command["request_key"], receipt_data)
    if replay:
        return (replay[0], replay[1])
    note = validated_note(receipt_data)
    with transaction.atomic():
        actor, handover = handover_for(
            actor, claims, handover_id, lock=True, write=True
        )
        replay = replay_operation(
            actor, operation, command["request_key"], receipt_data
        )
        if replay:
            return (replay[0], replay[1])
        from core_apps.common.command_authority import recheck_actor_session

        recheck_actor_session(actor, claims)
        if command["expected_revision"] != handover.revision:
            raise RentalConflict("Handover revision conflict.", code="stale_revision")
        if action not in handover_actions(actor, handover):
            raise RentalConflict("This handover action is no longer available.")
        approvals = set(handover.approvals)
        if action == "dispute":
            handover.status = RentalHandover.Status.DISPUTED
            handover.lease.occupancy_status = "handover_disputed"
        else:
            approvals.add(str(actor.id))
            handover.approvals = sorted(approvals)
            if {str(handover.lease.owner.id), str(handover.lease.tenant.id)}.issubset(
                approvals
            ):
                handover.status = RentalHandover.Status.ACCEPTED
                handover.accepted_at = timezone.now()
                if handover.kind == RentalHandover.Kind.MOVE_IN:
                    from .reputation.ancestry import freeze_handover

                    handover.context_snapshot = freeze_handover(handover)
                    handover.lease.occupancy_status = "occupied"
                else:
                    handover.lease.occupancy_status = "returned"
                    from ..models import RentalInventoryDayLock

                    RentalInventoryDayLock.objects.filter(
                        lease=handover.lease, kind=RentalInventoryDayLock.Kind.OCCUPIED
                    ).delete()
            else:
                handover.status = RentalHandover.Status.PENDING_APPROVAL
        handover.revision += 1
        handover.save()
        record_response_note(handover, actor, "handover", action, note)
        if (
            handover.kind == RentalHandover.Kind.MOVE_IN
            and handover.status == RentalHandover.Status.ACCEPTED
        ):
            evaluate_owner_payables(handover.lease)
        handover.lease.revision += 1
        handover.lease.save(
            update_fields=["occupancy_status", "revision", "updated_at"]
        )
        output = remember_mutation(
            user=actor,
            operation=operation,
            request_key=command["request_key"],
            payload=receipt_data,
            request_subject_id=handover.id,
            result_subject_id=handover.id,
            result_revision=handover.revision,
            resource=handover_payload(handover, actor),
        )
    return (output, 200)
