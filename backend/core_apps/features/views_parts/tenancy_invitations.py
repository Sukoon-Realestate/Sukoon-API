"""Views: tenancy invitations."""

from datetime import timedelta
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.properties.models import Property
from ..models import Lease, TenancyInvitation
from ..renderers import FeatureJsonRenderer
from ..serializers import TenancyInvitationCreateSerializer, TenancyInvitationSerializer
from ..services.tenancy_invitations import (
    InvitationConflict,
    LIVE_LEASE_STATUSES,
    create_notification_for_invitation,
    localized,
    refresh_effective_status,
    resolve_offer_snapshot,
    validate_accounts,
)
from .rental_operation_lookup import User, _replay, _remember, _paginate


from .tenancy_invitation_list import list_invitations


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def tenancy_invitations(request):
    if request.method == "GET":
        return list_invitations(request)

    if "interest_id" in request.data:
        from ..rental_phase2_views import create_interest_invitation

        return create_interest_invitation(request)
    serializer = TenancyInvitationCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data_in = serializer.validated_data
    property_obj = get_object_or_404(
        Property.objects.select_related("owner"),
        id=data_in["property_id"],
        owner=request.user,
    )
    tenant = get_object_or_404(User, id=data_in["tenant_id"])
    validate_accounts(request.user, tenant, request)
    replay = _replay(
        request.user,
        "tenancy_invitation.create",
        data_in["request_key"],
        request.data,
    )
    if replay:
        return replay
    from core_apps.properties.services.post_visit_decision import (
        validate_invitation_source,
        validate_visited_accommodation,
    )

    validate_invitation_source(property_obj, tenant, data_in)
    if property_obj.status != Property.Status.VERIFIED or not property_obj.is_verified:
        raise InvitationConflict(
            localized(
                request,
                "The property is not currently available for leasing.",
                "العقار غير متاح حاليًا للإيجار.",
            )
        )
    try:
        with transaction.atomic():
            property_obj = get_object_or_404(
                Property.objects.select_for_update().select_related("owner"),
                pk=property_obj.pk,
                owner=request.user,
            )
            tenant = get_object_or_404(User.objects.select_for_update(), pk=tenant.pk)
            validate_accounts(request.user, tenant, request)
            replay = _replay(
                request.user,
                "tenancy_invitation.create",
                data_in["request_key"],
                request.data,
            )
            if replay:
                return replay
            source_visit, source_decision = validate_invitation_source(
                property_obj, tenant, data_in, lock=True
            )
            if (
                property_obj.status != Property.Status.VERIFIED
                or not property_obj.is_verified
            ):
                raise InvitationConflict(
                    localized(
                        request,
                        "The property is not currently available for leasing.",
                        "العقار غير متاح حاليًا للإيجار.",
                    )
                )
            offer_id, snapshot = resolve_offer_snapshot(
                property_obj,
                data_in.get("offer_id", ""),
                data_in.get("expected_offer_revision"),
                request,
            )
            validate_visited_accommodation(source_visit, snapshot)
            if Lease.objects.filter(
                property=property_obj,
                offer_id=offer_id,
                status__in=LIVE_LEASE_STATUSES,
            ).exists():
                raise InvitationConflict(
                    localized(
                        request,
                        "The accommodation already has a conflicting lease.",
                        "يوجد عقد متعارض لمكان الإقامة.",
                    )
                )
            # Only join non-null relations under FOR UPDATE. Joining the optional
            # lease makes PostgreSQL reject the lock, even for an empty result.
            live = list(
                TenancyInvitation.objects.select_for_update()
                .filter(
                    owner=request.user,
                    property=property_obj,
                    tenant=tenant,
                    offer_id=offer_id,
                    status__in=[
                        TenancyInvitation.Status.PENDING,
                        TenancyInvitation.Status.ACCEPTED,
                    ],
                    lease__isnull=True,
                )
                .select_related("property", "property__owner", "owner", "tenant")
            )
            for existing in live:
                refresh_effective_status(existing)
            if any(
                item.status
                in [
                    TenancyInvitation.Status.PENDING,
                    TenancyInvitation.Status.ACCEPTED,
                ]
                for item in live
            ):
                raise InvitationConflict(
                    localized(
                        request,
                        "A live invitation already exists for this accommodation.",
                        "توجد دعوة سارية بالفعل لمكان الإقامة هذا.",
                    )
                )
            invitation = TenancyInvitation.objects.create(
                property=property_obj,
                owner=request.user,
                tenant=tenant,
                offer_id=offer_id,
                offer_snapshot=snapshot,
                expires_at=timezone.now() + timedelta(days=7),
                initiated_by=request.user,
                source_visit=source_visit,
                source_decision=source_decision,
                provenance_version="visit_decision_v1",
            )
            output = TenancyInvitationSerializer(
                invitation, context={"request": request}
            ).data
            _remember(
                request.user,
                "tenancy_invitation.create",
                data_in["request_key"],
                request.data,
                output,
                201,
                request_subject_id=property_obj.id,
                result_subject_id=invitation.id,
                result_revision=invitation.revision,
                is_rental_operation=True,
            )
            create_notification_for_invitation(request, invitation)
    except IntegrityError:
        replay = _replay(
            request.user,
            "tenancy_invitation.create",
            data_in["request_key"],
            request.data,
        )
        if replay:
            return replay
        raise InvitationConflict(
            localized(
                request,
                "A live invitation already exists for this accommodation.",
                "توجد دعوة سارية بالفعل لمكان الإقامة هذا.",
            )
        )
    return Response(output, status=status.HTTP_201_CREATED)
