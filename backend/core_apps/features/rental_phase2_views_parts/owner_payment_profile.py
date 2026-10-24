"""Rental phase2 views: owner payment profile."""

import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.notifications.services.notification_service import NotificationService
from ..models import (
    IdempotencyRecord,
    Lease,
    RentalInterest,
    RentalTimelineEvent,
    TenancyInvitation,
    TermsProposal,
)
from ..pagination import FeaturePagination
from ..providers import require_rental_provider, require_verified_rental_account
from ..renderers import FeatureJsonRenderer
from ..rental_serializers import OwnerPaymentProfileSerializer
from ..services.rental_phase2 import (
    RentalConflict,
    fingerprint,
    get_or_create_owner_profile,
    replay_operation,
)


def _paginate(request, queryset, serializer_class):
    paginator = FeaturePagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


def _replay_response(user, operation, request_key, payload):
    replay = replay_operation(user, operation, request_key, payload)
    if replay:
        data, response_status = replay
        return Response(data, status=response_status)
    return None


def _remember_session(
    *,
    user,
    operation,
    request_key,
    payload,
    request_subject_id,
    result_subject_id,
    result_revision,
    response_data,
    response_status=201,
):
    record = IdempotencyRecord.objects.create(
        user=user,
        operation=operation,
        request_key=str(request_key),
        fingerprint=fingerprint(payload),
        response_data={},
        response_status=response_status,
        is_rental_operation=True,
        request_subject_id=request_subject_id,
        result_subject_id=result_subject_id,
        result_revision=result_revision,
    )
    response_data["operation_receipt_id"] = str(record.id)
    # Keep the historical flat projection while supplying the canonical
    # session/receipt envelope consumed by Flutter create operations.
    response_data = {
        **response_data,
        "resource": dict(response_data),
        "operation_receipt": {
            "id": str(record.id),
            "subject_id": str(result_subject_id),
            "request_key": str(request_key),
            "revision": result_revision,
            "status": "confirmed",
        },
    }
    record.response_data = response_data
    record.save(update_fields=["response_data", "updated_at"])
    return response_data


def _participant_interest(request, interest_id, lock=False, *, provider_required=True):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if provider_required:
            require_rental_provider(request.user)
        else:
            require_verified_rental_account(request.user)
    queryset = RentalInterest.objects.select_related("property__owner", "tenant")
    if lock:
        queryset = queryset.select_for_update()
    interest = get_object_or_404(queryset, id=interest_id)
    if request.user not in (interest.tenant, interest.property.owner):
        raise NotFound()
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        from ..services.shared_housing.access import guard_individual
        guard_individual(interest)
    return interest


def _participant_proposal(request, proposal_id, lock=False):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        require_rental_provider(request.user)
    queryset = TermsProposal.objects.select_related(
        "owner", "interest__tenant", "interest__property"
    )
    if lock:
        from core_apps.properties.models import Property

        root = get_object_or_404(queryset, id=proposal_id)
        if request.user not in (root.owner, root.interest.tenant):
            raise NotFound()
        Property.objects.select_for_update().get(pk=root.interest.property_id)
        queryset = queryset.select_for_update(of=("self",))
    proposal = get_object_or_404(queryset, id=proposal_id)
    if request.user not in (proposal.owner, proposal.interest.tenant):
        raise NotFound()
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        from ..services.shared_housing.access import guard_individual
        guard_individual(proposal.interest)
    return proposal


def _participant_lease(request, lease_id, lock=False):
    from ..services.rental_lifecycle.locks import require_personal_workflow

    require_personal_workflow(
        get_object_or_404(Lease, id=lease_id, renter_company__isnull=True)
    )
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        require_rental_provider(request.user)
    queryset = Lease.objects.select_related("property", "owner", "tenant")
    if lock:
        from core_apps.properties.models import Property

        root = get_object_or_404(Lease, id=lease_id)
        if request.user not in (root.owner, root.tenant):
            raise NotFound()
        Property.objects.select_for_update().get(pk=root.property_id)
        queryset = queryset.select_for_update(of=("self",))
    lease = get_object_or_404(queryset, id=lease_id)
    if request.user not in (lease.owner, lease.tenant):
        raise NotFound()
    return lease


from ..services.rental_lifecycle.terms import (
    money_minor_from_offer as _money_minor_from_offer,
    validate_terms_offer as _validate_terms_offer,
    _json_safe,
)


def _event(lease, actor, kind, label, resource_id=None, description=""):
    RentalTimelineEvent.objects.create(
        lease=lease,
        actor=actor,
        kind=kind,
        label=label,
        description=description,
        resource_id=resource_id or lease.id,
    )


def _notify(user, notification_type, title, action_type, target_id, **context):
    payload = {
        "action_type": action_type,
        "target_id": str(target_id),
        **{key: str(value) for key, value in context.items() if value is not None},
    }
    if context.get("lease_id"):
        invitation = (
            TenancyInvitation.objects.filter(lease__id=context["lease_id"])
            .select_related("source_visit", "source_decision")
            .first()
        )
        if invitation and invitation.source_visit_id:
            payload["source_visit_id"] = str(invitation.source_visit.id)
            payload["source_decision_id"] = str(invitation.source_decision.id)
    NotificationService.create_notification(
        user=user,
        notification_type=notification_type,
        title=title,
        data=payload,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def owner_payment_profile(request):
    profile = get_or_create_owner_profile(request.user)
    return Response(
        OwnerPaymentProfileSerializer(profile, context={"request": request}).data
    )
