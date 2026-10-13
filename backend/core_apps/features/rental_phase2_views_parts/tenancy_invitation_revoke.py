"""Rental phase2 views: tenancy invitation revoke."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import TenancyInvitation
from ..renderers import FeatureJsonRenderer
from ..rental_serializers import RentalDecisionSerializer
from ..serializers import TenancyInvitationSerializer
from ..services.lease_permissions import can_revoke_invitation
from ..services.rental_phase2 import RentalConflict, remember_mutation
from .owner_payment_profile import _replay_response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def tenancy_invitation_revoke(request, invitation_id):
    if not request.user.is_active or not request.user.is_verified:
        raise PermissionDenied("A verified active owner account is required.")
    serializer = RentalDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    operation = f"rental_invitation.revoke.{invitation_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        invitation = get_object_or_404(
            TenancyInvitation.objects.select_for_update(of=("self",)).select_related(
                "property", "owner", "tenant", "lease"
            ),
            id=invitation_id,
            owner=request.user,
        )
        replay = _replay_response(
            request.user, operation, data["request_key"], request.data
        )
        if replay:
            return replay
        if data["decision"] != "revoke_invitation":
            raise ValidationError({"decision": "Must be revoke_invitation."})
        if data["expected_revision"] != invitation.revision:
            raise RentalConflict("Invitation revision conflict.", code="stale_revision")
        if invitation.lease_id or invitation.consumed_at:
            raise RentalConflict(
                "A consumed invitation cannot be revoked.", code="invitation_consumed"
            )
        if invitation.expires_at <= timezone.now():
            raise RentalConflict("The invitation expired.", code="invitation_expired")
        if not can_revoke_invitation(request.user, invitation):
            raise RentalConflict("This invitation can no longer be revoked.")
        invitation.status = TenancyInvitation.Status.REVOKED
        invitation.revoked_at = timezone.now()
        invitation.revision += 1
        invitation.save(
            update_fields=["status", "revoked_at", "revision", "updated_at"]
        )
        resource = TenancyInvitationSerializer(
            invitation, context={"request": request}
        ).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=invitation.id,
            result_subject_id=invitation.id,
            result_revision=invitation.revision,
            resource=resource,
        )
    return Response(output)
