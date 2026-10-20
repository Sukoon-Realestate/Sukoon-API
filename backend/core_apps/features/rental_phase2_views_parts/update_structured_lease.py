"""Rental phase2 views: update structured lease."""

from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import Lease, RentalInventoryDayLock, TenancyInvitation
from ..renderers import FeatureJsonRenderer
from ..rental_serializers import (
    LeasePhase2Serializer,
    RentalAgreementDraftBodySerializer,
    RentalDecisionSerializer,
)
from ..services.rental_phase2 import (
    RentalConflict,
    remember_mutation,
    reserve_inventory_days,
)
from ..services.tenancy_invitations import resolve_offer_snapshot
from ..services.platform_rent_payments import reviewed_terms
from .owner_payment_profile import (
    _replay_response,
    _participant_lease,
    _json_safe,
    _validate_terms_offer,
    _event,
)


def update_structured_lease(request, lease_id):
    serializer = RentalAgreementDraftBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    visible = _participant_lease(request, lease_id)
    if request.user != visible.owner:
        raise PermissionDenied("Only the owner can edit the draft.")
    operation = f"rental_agreement.update.{lease_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        lease = _participant_lease(request, lease_id, lock=True)
        if lease.status != Lease.Status.DRAFT or lease.legacy_read_only:
            raise RentalConflict("Only a new workflow draft can be edited.")
        if data["expected_revision"] != lease.revision:
            raise RentalConflict("Lease revision conflict.", code="stale_revision")
        invitation = get_object_or_404(
            TenancyInvitation.objects.select_for_update(),
            id=data["invitation_id"],
            lease=lease,
        )
        if data["invitation_revision"] != invitation.revision:
            raise RentalConflict("Invitation revision conflict.", code="stale_revision")
        if str(data["property_id"]) != str(lease.property.id) or str(
            data["tenant_id"]
        ) != str(lease.tenant.id):
            raise ValidationError("Participants and property cannot be changed.")
        if data["offer_id"] != lease.offer_id:
            raise ValidationError({"offer_id": "The accommodation cannot be changed."})
        _, snapshot = resolve_offer_snapshot(
            lease.property, data["offer_id"], data["offer_revision"], request
        )
        from core_apps.properties.services.post_visit_decision import (
            accommodation_identity,
        )

        if accommodation_identity(snapshot or {}) != accommodation_identity(
            lease.offer_snapshot or {}
        ):
            raise RentalConflict(
                "The accommodation cannot be changed.", code="accommodation_changed"
            )
        _validate_terms_offer(data["terms"], snapshot)
        RentalInventoryDayLock.objects.filter(lease=lease).delete()
        lease.start_date = data["terms"]["starts_on"]
        lease.end_date = data["terms"]["ends_on_exclusive"]
        lease.rent_amount_minor = data["terms"]["monthly_rent"]["amount_minor"]
        lease.terms = reviewed_terms(_json_safe(data["terms"]))
        lease.offer_snapshot = snapshot
        lease.reviewed_by = []
        lease.document_id = None
        lease.document_hash = ""
        lease.revision += 1
        lease.hold_expires_at = timezone.now() + timedelta(
            minutes=settings.RENTAL_HOLD_TTL_MINUTES
        )
        lease.save()
        reserve_inventory_days(
            lease, lease.start_date, lease.end_date, lease.hold_expires_at
        )
        _event(lease, request.user, "draft_updated", "Agreement draft updated")
        resource = LeasePhase2Serializer(lease, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=lease.id,
            result_revision=lease.revision,
            resource=resource,
        )
    return Response(output)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_review(request, lease_id):
    lease = _participant_lease(request, lease_id)
    serializer = RentalDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    operation = f"rental_agreement.review.{lease_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        lease = _participant_lease(request, lease_id, lock=True)
        if lease.legacy_read_only or lease.status != Lease.Status.DRAFT:
            raise RentalConflict("This agreement cannot be reviewed.")
        if data["expected_revision"] != lease.revision:
            raise RentalConflict("Lease revision conflict.", code="stale_revision")
        actor_id = str(request.user.id)
        from ..services.rental_lifecycle.consents import record_consent

        record_consent(lease, request.user, data["decision"])
        if data["decision"] == "accept_review":
            lease.reviewed_by = list(dict.fromkeys([*lease.reviewed_by, actor_id]))
        elif data["decision"] == "request_changes":
            lease.reviewed_by = []
        else:
            raise ValidationError({"decision": "Unsupported review decision."})
        lease.revision += 1
        lease.save(update_fields=["reviewed_by", "revision", "updated_at"])
        _event(lease, request.user, "review", data["decision"])
        resource = LeasePhase2Serializer(lease, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=lease.id,
            result_revision=lease.revision,
            resource=resource,
        )
    return Response(output)
