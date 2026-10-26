"""Resolve one tenant response, fencing late delivery before declaring absence."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.properties.models import Property
from ..models import IdempotencyRecord, TenancyInvitation
from ..renderers import FeatureJsonRenderer
from ..serializers import TenancyInvitationSerializer
from .tenancy_invitation_respond import _participant_invitation


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def tenancy_invitation_create_resolve(request):
    property_id = serializers.UUIDField().run_validation(
        request.data.get("property_id")
    )
    key = str(serializers.UUIDField().run_validation(request.data.get("request_key")))
    with transaction.atomic():
        property_obj = get_object_or_404(
            Property.objects.select_for_update(), id=property_id, owner=request.user
        )
        record, _ = IdempotencyRecord.objects.get_or_create(
            user=request.user,
            operation="tenancy_invitation.create",
            request_key=key,
            defaults={
                "fingerprint": "",
                "response_status": 409,
                "response_data": {},
                "is_rental_operation": True,
                "request_subject_id": property_obj.id,
                "recovery_status": IdempotencyRecord.RecoveryStatus.ABSENT_FINAL,
            },
        )
        if str(record.request_subject_id) != str(property_obj.id):
            raise ValidationError(
                {"request_key": "This key belongs to another property."}
            )
        invitation = None
        if record.recovery_status == IdempotencyRecord.RecoveryStatus.CONFIRMED:
            invitation = get_object_or_404(
                TenancyInvitation,
                id=record.result_subject_id,
                property=property_obj,
                owner=request.user,
            )
        response = Response(
            {
                "request_key": key,
                "property_id": str(property_obj.id),
                "status": record.recovery_status,
                "invitation": (
                    TenancyInvitationSerializer(
                        invitation, context={"request": request}
                    ).data
                    if invitation
                    else None
                ),
            }
        )
        response["Cache-Control"] = "private, no-store"
        return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def tenancy_invitation_response_resolve(request, invitation_id):
    visible = _participant_invitation(request, invitation_id)
    if request.user.pk != visible.tenant_id:
        raise PermissionDenied("Only the addressed tenant can recover their response.")
    key = str(serializers.UUIDField().run_validation(request.data.get("request_key")))
    operation = f"tenancy_invitation.respond.{invitation_id}"
    with transaction.atomic():
        # Same serialization point as respond. A request arriving after this
        # absence receipt encounters its tombstone before any business mutation.
        Property.objects.select_for_update().get(pk=visible.property_id)
        invitation = get_object_or_404(
            TenancyInvitation.objects.select_for_update(),
            pk=visible.pk,
            tenant=request.user,
        )
        record, _ = IdempotencyRecord.objects.get_or_create(
            user=request.user,
            operation=operation,
            request_key=key,
            defaults={
                "fingerprint": "",
                "response_status": 409,
                "response_data": {},
                "is_rental_operation": True,
                "request_subject_id": invitation.id,
                "result_subject_id": invitation.id,
                "result_revision": invitation.revision,
                "recovery_status": IdempotencyRecord.RecoveryStatus.ABSENT_FINAL,
            },
        )
        response = Response(
            {
                "request_key": key,
                "status": record.recovery_status,
                "decision": record.response_data.get("status", ""),
                "invitation": TenancyInvitationSerializer(
                    invitation, context={"request": request}
                ).data,
            }
        )
        response["Cache-Control"] = "private, no-store"
        return response
