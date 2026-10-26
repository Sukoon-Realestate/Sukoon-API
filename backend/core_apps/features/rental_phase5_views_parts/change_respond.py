"""Rental phase5 views: change respond."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from ..models import RentalChange, RentInvoice
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from ..services.rental_notes import record_response_note, validated_note
from .maintenance_action import change_payload, _change
from .change_collection import change_collection


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payment_extensions(request, lease_id):
    return change_collection(request, lease_id, RentalChange.Kind.PAYMENT_EXTENSION)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def amendments(request, lease_id):
    return change_collection(request, lease_id, RentalChange.Kind.AMENDMENT)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def renewals(request, lease_id):
    return change_collection(request, lease_id, RentalChange.Kind.RENEWAL)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def terminations(request, lease_id):
    return change_collection(request, lease_id, RentalChange.Kind.TERMINATION)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def external_claims(request, lease_id):
    return change_collection(request, lease_id, RentalChange.Kind.EXTERNAL_PAYMENT)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def external_claim_create(request, invoice_id):
    invoice = get_object_or_404(
        RentInvoice.objects.select_related("lease"), id=invoice_id, purpose="rent"
    )
    from ..services.platform_rent_payments import reject_external_claim

    return reject_external_claim(request, invoice)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def change_detail(request, change_id, kind):
    if request.method == "PATCH":
        from ..services.change_versions import ChangeEditBody, revise
        from ..services.rental_lifecycle.common import command
        from .maintenance_payload import _safe_evidence

        serializer = ChangeEditBody(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        def execute(item):
            item = revise(item, request.user, data, _safe_evidence(item.lease, data["evidence_ids"]))
            return item, change_payload(item, request.user), 200

        def parties():
            item = _change(request, change_id, kind)
            return {item.lease.owner_id, item.lease.tenant_id}

        output, response_status = command(
            user=request.user, operation=f"rental_change.edit.{change_id}", data=request.data,
            authorize=lambda: _change(request, change_id, kind, lock=True), execute=execute,
            account_parties=parties,
        )
        return Response(output, status=response_status)
    return Response(change_payload(_change(request, change_id, kind), request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def change_respond(request, change_id, kind):
    action = request.data.get("action") or request.data.get("decision")
    if action not in {"accept", "reject", "request_changes"} or not request.data.get(
        "request_key"
    ):
        raise ValidationError(
            "accept/reject/request_changes and request_key are required."
        )
    item = _change(request, change_id, kind)
    if kind == RentalChange.Kind.EXTERNAL_PAYMENT:
        from ..services.financial_authority import require_financial_actor

        finance_roles = {
            StaffProfile.RoleName.FINANCIAL_APPROVER,
            StaffProfile.RoleName.PSP_RECONCILIATION,
        }
        require_financial_actor(request.user, finance_roles, "external_payment.review")
    operation = f"rental_change.respond.{item.id}.{request.user.id}"
    note = validated_note(request.data)
    with transaction.atomic():
        if kind == RentalChange.Kind.EXTERNAL_PAYMENT:
            require_financial_actor(
                request.user, finance_roles, "external_payment.review", lock=True
            )
        item = _change(request, change_id, kind, lock=True)
        replay = replay_operation(
            request.user, operation, request.data["request_key"], request.data
        )
        if replay:
            return Response(replay[0], status=replay[1])
        if int(request.data.get("expected_revision", 0)) != item.revision:
            raise RentalConflict("Change revision conflict.", code="stale_revision")
        if item.status not in {
            RentalChange.Status.PROPOSED,
            RentalChange.Status.CHANGES_REQUESTED,
            RentalChange.Status.REVIEW_REQUIRED,
        }:
            raise RentalConflict("This change is no longer awaiting a response.")
        if kind != RentalChange.Kind.EXTERNAL_PAYMENT:
            from ..services.cycle_permissions import cycle_actions
            if action == "accept" and kind in {RentalChange.Kind.AMENDMENT, RentalChange.Kind.RENEWAL}:
                from ..services.change_terms import validate_changed_terms
                validate_changed_terms(item.terms)
                if item.previous_terms and item.previous_terms != item.lease.terms:
                    raise RentalConflict("The lease terms changed. The author must review and submit an updated proposal.", code="lease_changed")
            if action == "accept" and kind == RentalChange.Kind.PAYMENT_EXTENSION:
                if item.invoice.status in {"paid", "settled", "cancelled", "written_off"} or item.invoice.due_at != item.original_due_at:
                    raise RentalConflict("This invoice no longer matches the proposed payment extension.", code="invoice_changed")
            if action not in cycle_actions(request.user, item):
                raise PermissionDenied("Review the current proposal and your role before responding.")
        if action == "reject":
            item.status = RentalChange.Status.REJECTED
        elif action == "request_changes":
            item.status = RentalChange.Status.CHANGES_REQUESTED
            item.approvals = []
        elif kind == RentalChange.Kind.EXTERNAL_PAYMENT:
            item.status = RentalChange.Status.ACCEPTED
        else:
            if kind in {RentalChange.Kind.AMENDMENT, RentalChange.Kind.RENEWAL}:
                from ..services.change_terms import validate_changed_terms

                validate_changed_terms(item.terms)
            approvals = set(item.approvals)
            approvals.add(str(request.user.id))
            item.approvals = sorted(approvals)
            if {str(item.lease.owner.id), str(item.lease.tenant.id)}.issubset(
                approvals
            ):
                item.status = RentalChange.Status.ACCEPTED
                if kind == RentalChange.Kind.PAYMENT_EXTENSION:
                    item.invoice.deferred_until = item.deferred_until
                    item.invoice.revision += 1
                    item.invoice.save(
                        update_fields=["deferred_until", "revision", "updated_at"]
                    )
                    item.status = RentalChange.Status.APPLIED
                    item.applied_at = timezone.now()
                elif kind == RentalChange.Kind.TERMINATION:
                    from ..services.legal_lifecycle import accept_termination

                    accept_termination(item)
                    if item.effective_on <= timezone.localdate():
                        item.status = RentalChange.Status.APPLIED
                        item.applied_at = timezone.now()
        item.revision += 1
        item.save()
        from ..services.change_versions import freeze, snapshot
        from ..services.rental_lifecycle.consents import record_consent
        freeze(item, baseline=not item.versions.exists())
        record_consent(item, request.user, action, {**snapshot(item), "note": note})
        record_response_note(item, request.user, "change", action, note)
        from ..services.planning_notifications import record_event

        record_event(item, request.user, operation)
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request.data["request_key"],
            payload=request.data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=change_payload(item, request.user),
        )
    return Response(output)
