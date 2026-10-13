"""Views: tenancy invitation respond."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import Lease, TenancyInvitation
from ..renderers import FeatureJsonRenderer
from ..serializers import (
    TenancyInvitationResponseSerializer,
    TenancyInvitationSerializer,
)
from ..services.tenancy_invitations import (
    InvitationConflict,
    create_notification_for_response,
    refresh_effective_status,
)
from .rental_operation_lookup import _replay, _remember


def _participant_invitation(request, invitation_id):
    invitation = get_object_or_404(
        TenancyInvitation.objects.select_related(
            "property", "property__owner", "owner", "tenant", "lease"
        ),
        id=invitation_id,
    )
    if request.user not in (invitation.owner, invitation.tenant):
        raise NotFound()
    return invitation


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def tenancy_invitation_detail(request, invitation_id):
    invitation = _participant_invitation(request, invitation_id)
    refresh_effective_status(invitation)
    return Response(
        TenancyInvitationSerializer(invitation, context={"request": request}).data
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def tenancy_invitation_respond(request, invitation_id):
    visible = _participant_invitation(request, invitation_id)
    if request.user != visible.tenant:
        raise PermissionDenied("Only the addressed tenant can respond.")
    if not request.user.is_active or not request.user.is_verified:
        raise PermissionDenied("A verified active tenant account is required.")
    serializer = TenancyInvitationResponseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data_in = serializer.validated_data
    operation = f"tenancy_invitation.respond.{invitation_id}"
    replay = _replay(request.user, operation, data_in["request_key"], request.data)
    if replay:
        return replay
    with transaction.atomic():
        invitation = get_object_or_404(
            TenancyInvitation.objects.select_for_update().select_related(
                "property", "property__owner", "owner", "tenant"
            ),
            id=invitation_id,
            tenant=request.user,
        )
        replay = _replay(request.user, operation, data_in["request_key"], request.data)
        if replay:
            return replay
        refresh_effective_status(invitation)
        if invitation.status != TenancyInvitation.Status.PENDING:
            return Response(
                {"message": "This invitation can no longer be answered."},
                status=status.HTTP_409_CONFLICT,
            )
        if data_in["revision"] != invitation.revision:
            raise InvitationConflict("Invitation revision conflict.")
        now = timezone.now()
        invitation.status = data_in["decision"]
        invitation.revision += 1
        invitation.responded_by = request.user
        fields = ["status", "revision", "responded_by", "updated_at"]
        if invitation.status == TenancyInvitation.Status.ACCEPTED:
            invitation.accepted_at = now
            fields.append("accepted_at")
        else:
            invitation.rejected_at = now
            fields.append("rejected_at")
        invitation.save(update_fields=fields)
        output = TenancyInvitationSerializer(
            invitation, context={"request": request}
        ).data
        _remember(
            request.user,
            operation,
            data_in["request_key"],
            request.data,
            output,
            200,
            request_subject_id=invitation.id,
            result_subject_id=invitation.id,
            result_revision=invitation.revision,
            is_rental_operation=True,
        )
        create_notification_for_response(request, invitation)
    return Response(output)


def _lease_queryset(user, workspace):
    if workspace == "owner":
        return Lease.objects.filter(owner=user)
    if workspace == "tenant":
        return Lease.objects.filter(tenant=user)
    raise ValidationError({"workspace": "Must be owner or tenant."})
