"""Rental phase5 views: maintenance action."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from ..models import Lease, MaintenanceEvent, MaintenanceRequest, RentalChange
from ..renderers import FeatureJsonRenderer
from ..services.cycle_permissions import MAINTENANCE_TRANSITIONS, cycle_actions
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .maintenance_payload import (
    MAINTENANCE_ACTIONS,
    _money,
    maintenance_payload,
    _maintenance,
)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def maintenance_action(request, request_id):
    action = request.data.get("action") or request.data.get("decision")
    if action not in MAINTENANCE_ACTIONS or not request.data.get("request_key"):
        raise ValidationError({"action": "Unsupported action or missing request key."})
    item = _maintenance(request, request_id)
    operation = f"maintenance.action.{item.id}.{action}"
    replay = replay_operation(
        request.user, operation, request.data["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    transitions = MAINTENANCE_TRANSITIONS
    with transaction.atomic():
        item = _maintenance(request, request_id, lock=True)
        if int(request.data.get("expected_revision", 0)) != item.revision:
            raise RentalConflict(
                "Maintenance revision conflict.", code="stale_revision"
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
            cost = request.data.get("cost", {})
            payer = request.data.get("cost_payer")
            if (
                payer not in {"owner", "tenant"}
                or not isinstance(cost.get("amount_minor"), int)
                or cost["amount_minor"] <= 0
            ):
                raise ValidationError(
                    "A positive EGP cost and owner/tenant payer are required."
                )
            item.proposed_cost_minor = cost["amount_minor"]
            item.cost_payer = payer
            item.cost_version += 1
            item.approved_cost_version = None
        elif action in {"approve_cost", "reject_cost"}:
            responsible = (
                item.lease.owner if item.cost_payer == "owner" else item.lease.tenant
            )
            if request.user != responsible:
                raise PermissionDenied(
                    "Only the responsible payer may decide this cost."
                )
            if (
                int(request.data.get("cost_version", 0)) != item.cost_version
                or not item.proposed_cost_minor
            ):
                raise RentalConflict("Cost version conflict.", code="stale_revision")
            item.approved_cost_version = (
                item.cost_version if action == "approve_cost" else None
            )
        if action == "propose_appointment":
            if not request.data.get("appointment_at"):
                raise ValidationError({"appointment_at": "Required."})
            item.appointment_at = parse_datetime(request.data["appointment_at"])
            if not item.appointment_at:
                raise ValidationError({"appointment_at": "Must be an ISO date-time."})
        item.revision += 1
        item.save()
        MaintenanceEvent.objects.create(
            maintenance_request=item,
            actor=request.user,
            action=action,
            note=request.data.get("note", ""),
            appointment_at=(
                item.appointment_at
                if action in {"propose_appointment", "accept_appointment"}
                else None
            ),
            cost_minor=item.proposed_cost_minor if "cost" in action else None,
            metadata={"cost_version": item.cost_version} if "cost" in action else {},
        )
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request.data["request_key"],
            payload=request.data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=maintenance_payload(item, request.user),
        )
    return Response(output)


def change_payload(item, user=None):
    return {
        "allowed_actions": cycle_actions(user, item),
        "blocking_reasons": [],
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "invoice_id": str(item.invoice.id) if item.invoice else None,
        "revision": item.revision,
        "kind": item.kind,
        "status": item.status,
        "reason": item.reason,
        "requested_date": str(item.requested_date) if item.requested_date else None,
        "original_due_at": (
            item.original_due_at.isoformat() if item.original_due_at else None
        ),
        "deferred_until": (
            item.deferred_until.isoformat() if item.deferred_until else None
        ),
        "effective_on": str(item.effective_on) if item.effective_on else None,
        "amount": _money(item.amount_minor),
        "terms": item.terms,
        "previous_terms": item.previous_terms,
        "document_id": str(item.document_id) if item.document_id else None,
        "document_hash": item.document_hash,
        "signature_document_id": str(item.document_id) if item.document_id else None,
        "accepted_by": item.approvals,
        "signed_by": item.signed_by,
    }


def _change(request, change_id, expected_kind=None, lock=False):
    queryset = RentalChange.objects.select_related(
        "lease__owner", "lease__tenant", "invoice"
    )
    item = get_object_or_404(queryset, id=change_id)
    if expected_kind and item.kind != expected_kind:
        raise NotFound()
    profile = getattr(request.user, "staff_profile", None)
    operations_external = item.kind == RentalChange.Kind.EXTERNAL_PAYMENT and (
        request.user.is_superuser
        or (
            profile
            and profile.is_active
            and profile.role_name
            in {
                StaffProfile.RoleName.FINANCIAL_APPROVER,
                StaffProfile.RoleName.PSP_RECONCILIATION,
            }
        )
    )
    if (
        request.user not in (item.lease.owner, item.lease.tenant)
        and not operations_external
    ):
        raise NotFound()
    if lock:
        lease = Lease.objects.select_for_update().get(pk=item.lease_id)
        item = queryset.select_for_update(of=("self",)).get(pk=item.pk)
        item.lease = lease
    return item
