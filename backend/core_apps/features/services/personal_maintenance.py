"""Personal maintenance commands own receipts, root locks and durable state."""

from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..models import MaintenanceEvent, MaintenanceRequest
from .rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .cycle_permissions import MAINTENANCE_TRANSITIONS, cycle_actions
from .maintenance_access import access_window_current, appointment_reviewable
from .commands import money_minor
from .maintenance_reads import (
    lease_for,
    maintenance_for,
    _safe_evidence,
    maintenance_payload,
)


def create_request(actor, claims, lease, command, receipt_data):
    from .cycle_permissions import cycle_actions
    from rest_framework.exceptions import PermissionDenied

    if "create_maintenance_request" not in cycle_actions(actor, lease):
        raise PermissionDenied(
            "Maintenance requires an existing serviceable agreement."
        )
    operation = f"maintenance.create.{lease.id}"
    replay = replay_operation(actor, operation, command["request_key"], receipt_data)
    if replay:
        return (replay[0], replay[1])
    evidence = _safe_evidence(lease, command["evidence_ids"])
    with transaction.atomic():
        lease = lease_for(actor, lease.id, lock=True, servicing=True, write=True)
        if "create_maintenance_request" not in cycle_actions(actor, lease):
            raise PermissionDenied(
                "Maintenance requires an existing serviceable agreement."
            )
        replay = replay_operation(
            actor, operation, command["request_key"], receipt_data
        )
        if replay:
            return (replay[0], replay[1])
        from core_apps.common.command_authority import recheck_actor_session

        recheck_actor_session(actor, claims)
        item = MaintenanceRequest.objects.create(
            lease=lease,
            reporter=actor,
            title=command["title"],
            description=command["description"],
            category=command["category"],
            priority=command["priority"],
            access_times=command["access_times"],
        )
        item.evidence.set(evidence)
        MaintenanceEvent.objects.create(
            maintenance_request=item, actor=actor, action="created"
        )
        output = remember_mutation(
            user=actor,
            operation=operation,
            request_key=command["request_key"],
            payload=receipt_data,
            request_subject_id=lease.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=maintenance_payload(item, actor),
            response_status=201,
        )
    return (output, status.HTTP_201_CREATED)


def apply_action(actor, claims, request_id, action, command, receipt_data):
    item = maintenance_for(actor, request_id)
    operation = f"maintenance.action.{item.id}.{action}"
    replay = replay_operation(actor, operation, command["request_key"], receipt_data)
    if replay:
        return (replay[0], replay[1])
    transitions = MAINTENANCE_TRANSITIONS
    with transaction.atomic():
        item = maintenance_for(actor, request_id, lock=True)
        replay = replay_operation(
            actor, operation, command["request_key"], receipt_data
        )
        if replay:
            return (replay[0], replay[1])
        from core_apps.common.command_authority import recheck_actor_session

        recheck_actor_session(actor, claims)
        if command["expected_revision"] != item.revision:
            raise RentalConflict(
                "Maintenance revision conflict.", code="stale_revision"
            )
        if action in transitions and item.status not in transitions[action][0]:
            raise RentalConflict("Unsupported maintenance transition.")
        if action == "start_work" and (
            not access_window_current(item)
            or (
                item.proposed_cost_minor
                and item.cost_version != item.approved_cost_version
            )
        ):
            raise RentalConflict(
                "Current access consent and cost approval are required.",
                code="consent_required",
            )
        if action == "accept_appointment" and (not appointment_reviewable(item)):
            raise RentalConflict(
                "Review a new bounded appointment before approving access.",
                code="appointment_expired",
            )
        if action == "report_missed" and (not command["note"].strip()):
            raise ValidationError({"note": "Describe the missed appointment."})
        if action in {"approve_cost", "reject_cost"}:
            responsible = (
                item.lease.owner if item.cost_payer == "owner" else item.lease.tenant
            )
            if actor != responsible or not actor.is_active or (not actor.is_verified):
                raise PermissionDenied(
                    "Only the current responsible payer may decide this cost."
                )
            if "cost_version" not in command:
                raise ValidationError({"cost_version": "This field is required."})
            if (
                command["cost_version"] != item.cost_version
                or not item.proposed_cost_minor
                or item.approved_cost_version == item.cost_version
            ):
                raise RentalConflict("Cost version conflict.", code="stale_revision")
        if action not in cycle_actions(actor, item):
            raise PermissionDenied(
                "This action is not permitted for the current actor, access consent and cost version."
            )
        if action in transitions:
            allowed, target = transitions[action]
            if item.status not in allowed:
                raise RentalConflict("Unsupported maintenance transition.")
            item.status = target
        elif action == "reply":
            if item.status == MaintenanceRequest.Status.CANCELLED:
                raise RentalConflict("Cancelled requests cannot receive replies.")
        elif action == "propose_cost":
            from .billing_sources import invalidate_maintenance_cost

            invalidate_maintenance_cost(item)
            amount = money_minor(command.get("cost", {}))
            payer = command.get("cost_payer")
            if payer not in {"owner", "tenant"} or amount <= 0:
                raise ValidationError(
                    "A positive EGP cost and owner/tenant payer are required."
                )
            item.proposed_cost_minor = amount
            item.cost_payer = payer
            item.cost_version += 1
            item.approved_cost_version = None
        elif action in {"approve_cost", "reject_cost"}:
            item.approved_cost_version = (
                item.cost_version if action == "approve_cost" else None
            )
        if action == "propose_appointment":
            if not command.get("appointment_at"):
                raise ValidationError({"appointment_at": "Required."})
            item.appointment_at = command["appointment_at"]
            item.appointment_ends_at = command.get("appointment_ends_at")
            from django.utils import timezone

            if (
                item.appointment_at <= timezone.now()
                or not item.appointment_ends_at
                or item.appointment_ends_at <= item.appointment_at
            ):
                raise ValidationError(
                    {
                        "appointment_at": "Use future start and end date-times with their timezones."
                    }
                )
            item.appointment_version += 1
            item.access_approved_version = None
        elif action == "accept_appointment":
            item.access_approved_version = item.appointment_version
        elif action == "report_missed":
            item.access_approved_version = None
        if action in {"cancel", "reject_cost"}:
            from .billing_sources import invalidate_maintenance_cost

            invalidate_maintenance_cost(item)
        item.revision += 1
        item.save()
        if action == "approve_cost":
            from .billing_sources import maintenance_invoice

            maintenance_invoice(item, actor)
        from .rental_lifecycle.common import audit

        audit(
            item,
            actor,
            f"maintenance.{action}",
            command["note"],
            {
                "appointment_version": item.appointment_version,
                "access_approved_version": item.access_approved_version,
                "appointment_ends_at": (
                    item.appointment_ends_at.isoformat()
                    if item.appointment_ends_at
                    else None
                ),
                "cost_version": item.cost_version,
                "approved_cost_version": item.approved_cost_version,
            },
        )
        MaintenanceEvent.objects.create(
            maintenance_request=item,
            actor=actor,
            action=action,
            note=command["note"],
            appointment_at=(
                item.appointment_at
                if action in {"propose_appointment", "accept_appointment"}
                else None
            ),
            cost_minor=item.proposed_cost_minor if "cost" in action else None,
            metadata=(
                {"cost_version": item.cost_version}
                if "cost" in action
                else {
                    "appointment_version": item.appointment_version,
                    "appointment_ends_at": (
                        item.appointment_ends_at.isoformat()
                        if item.appointment_ends_at
                        else None
                    ),
                }
            ),
        )
        output = remember_mutation(
            user=actor,
            operation=operation,
            request_key=command["request_key"],
            payload=receipt_data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=maintenance_payload(item, actor),
        )
    return (output, 200)
