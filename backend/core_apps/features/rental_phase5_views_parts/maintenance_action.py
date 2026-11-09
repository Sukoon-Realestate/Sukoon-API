"""Rental phase5 views: maintenance action."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from ..models import (
    Lease,
    MaintenanceEvent,
    MaintenanceRequest,
    RentalChange,
    RentInvoice,
    PrivateAccessRevocation,
)
from ..renderers import FeatureJsonRenderer
from ..services.cycle_permissions import MAINTENANCE_TRANSITIONS, cycle_actions
from ..services.maintenance_access import access_window_current, appointment_reviewable
from ..services.commands import money_minor
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
    from ..rental_serializers_parts.command_serializers import (
        MaintenanceActionCommand,
        validated,
    )

    data = request.data if hasattr(request.data, "get") else {}
    action = data.get("action") or data.get("decision")
    if not isinstance(action, str) or action not in MAINTENANCE_ACTIONS:
        raise ValidationError({"action": "Unsupported action or missing request key."})
    # A3-02: type every field before the lock, receipt or any write.
    # Action-specific fields are typed only for the action that uses them, so
    # values other actions ignored before still do not turn into errors.
    used = {
        "propose_appointment": {"appointment_at", "appointment_ends_at"},
        "propose_cost": {"cost", "cost_payer"},
        "approve_cost": {"cost_version"},
        "reject_cost": {"cost_version"},
    }.get(action, set())
    ignored = {"appointment_at", "appointment_ends_at", "cost", "cost_payer", "cost_version"} - used
    command = validated(
        MaintenanceActionCommand,
        {key: data.get(key) for key in data if key not in ignored},
    )
    item = _maintenance(request, request_id)
    operation = f"maintenance.action.{item.id}.{action}"
    replay = replay_operation(
        request.user, operation, command["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    transitions = MAINTENANCE_TRANSITIONS
    with transaction.atomic():
        item = _maintenance(request, request_id, lock=True)
        replay = replay_operation(
            request.user, operation, command["request_key"], request.data
        )
        if replay:
            return Response(replay[0], status=replay[1])
        from core_apps.common.command_authority import recheck_session

        recheck_session(request)
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
        if action == "accept_appointment" and not appointment_reviewable(item):
            raise RentalConflict(
                "Review a new bounded appointment before approving access.",
                code="appointment_expired",
            )
        if action == "report_missed" and not command["note"].strip():
            raise ValidationError({"note": "Describe the missed appointment."})
        if action in {"approve_cost", "reject_cost"}:
            responsible = (
                item.lease.owner if item.cost_payer == "owner" else item.lease.tenant
            )
            if (
                request.user != responsible
                or not request.user.is_active
                or not request.user.is_verified
            ):
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
        if action not in cycle_actions(request.user, item):
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
            from ..services.billing_sources import invalidate_maintenance_cost
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
            from ..services.billing_sources import invalidate_maintenance_cost
            invalidate_maintenance_cost(item)
        item.revision += 1
        item.save()
        if action == "approve_cost":
            from ..services.billing_sources import maintenance_invoice
            maintenance_invoice(item, request.user)
        from ..services.rental_lifecycle.common import audit

        audit(
            item,
            request.user,
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
            actor=request.user,
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
            user=request.user,
            operation=operation,
            request_key=command["request_key"],
            payload=request.data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=maintenance_payload(item, request.user),
        )
    return Response(output)


def change_payload(item, user=None):
    from core_apps.common.translation import translate_message
    from ..services.signing_documents import projection
    from ..services.change_terms import changed_terms_blocker
    from ..services.change_versions import history, comments
    from ..services.version_comparison import rental_change_comparison
    from ..rental_phase4_views_parts.handover_payload import evidence_payload
    from ..services.termination_notice import projection as notice_projection

    blocker = changed_terms_blocker(item)
    termination_notice = notice_projection(item, user)
    return {
        "allowed_actions": cycle_actions(user, item),
        "blocking_reasons": ([translate_message(blocker)] if blocker else []) + (termination_notice.get("blocking_reasons", []) if termination_notice else []),
        "termination_notice": termination_notice,
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "invoice_id": str(item.invoice.id) if item.invoice else None,
        "revision": item.revision,
        "content_revision": item.content_revision,
        "requester_id": str(item.requester.id),
        "history": history(item),
        "comments": comments(item),
        "evidence_ids": [str(value) for value in item.evidence.values_list("id", flat=True)],
        "evidence": [evidence_payload(value) for value in item.evidence.all()],
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
        "comparison": rental_change_comparison(item),
        "document_id": str(item.document_id) if item.document_id else None,
        "signing_document": projection(item, user),
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
    from ..services.rental_lifecycle.locks import require_personal_workflow
    require_personal_workflow(item.lease)
    if expected_kind and item.kind != expected_kind:
        raise NotFound()
    if lock:
        lease = Lease.objects.select_for_update().get(pk=item.lease_id)
        item = queryset.select_for_update(of=("self",)).get(pk=item.pk)
        item.lease = lease
        if item.invoice_id:
            item.invoice = RentInvoice.objects.select_for_update().get(pk=item.invoice_id)
    from core_apps.users.models import User

    current = User.objects.get(pk=request.user.pk)
    if (
        not current.is_active
        or PrivateAccessRevocation.objects.filter(
            lease=item.lease, user=current
        ).exists()
    ):
        raise NotFound()
    operations_external = item.kind == RentalChange.Kind.EXTERNAL_PAYMENT and (
        current.is_superuser
        or StaffProfile.objects.filter(
            user=current,
            is_active=True,
            role_name__in={
                StaffProfile.RoleName.FINANCIAL_APPROVER,
                StaffProfile.RoleName.PSP_RECONCILIATION,
            },
        ).exists()
    )
    if (
        current.pk not in (item.lease.owner_id, item.lease.tenant_id)
        and not operations_external
    ):
        raise NotFound()
    return item
