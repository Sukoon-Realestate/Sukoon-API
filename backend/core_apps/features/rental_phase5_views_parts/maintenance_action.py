"""Rental phase5 views: maintenance action."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from ..models import Lease, RentalChange, RentInvoice, PrivateAccessRevocation
from ..renderers import FeatureJsonRenderer
from ..services.cycle_permissions import cycle_actions
from .maintenance_payload import MAINTENANCE_ACTIONS, _money


class MaintenanceActionView(FeatureAPIView):
    name = "Maintenance Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "maintenance_action",
            "maintenance_action",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def post(self, request, request_id):
        from ..rental_serializers_parts.command_serializers import (
            MaintenanceActionCommand,
            validated,
        )

        data = request.data if hasattr(request.data, "get") else {}
        action = data.get("action") or data.get("decision")
        if not isinstance(action, str) or action not in MAINTENANCE_ACTIONS:
            raise ValidationError(
                {"action": "Unsupported action or missing request key."}
            )
        # A3-02: type every field before the lock, receipt or any write.
        # Action-specific fields are typed only for the action that uses them, so
        # values other actions ignored before still do not turn into errors.
        used = {
            "propose_appointment": {"appointment_at", "appointment_ends_at"},
            "propose_cost": {"cost", "cost_payer"},
            "approve_cost": {"cost_version"},
            "reject_cost": {"cost_version"},
        }.get(action, set())
        ignored = {
            "appointment_at",
            "appointment_ends_at",
            "cost",
            "cost_payer",
            "cost_version",
        } - used
        command = validated(
            MaintenanceActionCommand,
            {key: data.get(key) for key in data if key not in ignored},
        )
        from ..services.personal_maintenance import apply_action

        payload, status = apply_action(
            request.user, request.auth, request_id, action, command, request.data
        )
        return Response(payload, status=status)


# Stable callable import for integrations; URLs use the explicit class.
maintenance_action = MaintenanceActionView.as_view()


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
        "blocking_reasons": ([translate_message(blocker)] if blocker else [])
        + (
            termination_notice.get("blocking_reasons", []) if termination_notice else []
        ),
        "termination_notice": termination_notice,
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "invoice_id": str(item.invoice.id) if item.invoice else None,
        "revision": item.revision,
        "content_revision": item.content_revision,
        "requester_id": str(item.requester.id),
        "history": history(item),
        "comments": comments(item),
        "evidence_ids": [
            str(value) for value in item.evidence.values_list("id", flat=True)
        ],
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
            item.invoice = RentInvoice.objects.select_for_update().get(
                pk=item.invoice_id
            )
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
