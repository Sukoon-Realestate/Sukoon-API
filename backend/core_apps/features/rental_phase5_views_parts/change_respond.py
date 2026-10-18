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
    mutable = request.data.copy()
    mutable["invoice_id"] = str(invoice.id)
    request._full_data = mutable
    return change_collection(
        request, invoice.lease.id, RentalChange.Kind.EXTERNAL_PAYMENT
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def change_detail(request, change_id, kind):
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
