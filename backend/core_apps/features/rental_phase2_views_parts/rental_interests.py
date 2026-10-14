"""Rental phase2 views: rental interests."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.properties.models import Property
from core_apps.notifications.models import Notification
from ..models import RentalInterest
from ..providers import require_verified_rental_account
from ..renderers import FeatureJsonRenderer
from ..rental_serializers import (
    RentalDecisionSerializer,
    RentalInterestBodySerializer,
    RentalInterestSerializer,
)
from ..services.rental_phase2 import (
    RentalConflict,
    remember_mutation,
    validate_interest_capacity,
)
from ..services.lease_permissions import interest_actions, interest_creation_blocker
from ..services.tenancy_invitations import resolve_offer_snapshot
from .owner_payment_profile import (
    _paginate,
    _replay_response,
    _participant_interest,
    _notify,
)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_interests(request):
    if request.method == "GET":
        workspace = request.query_params.get("workspace")
        if workspace == "tenant":
            queryset = RentalInterest.objects.filter(tenant=request.user)
        elif workspace == "owner":
            queryset = RentalInterest.objects.filter(property__owner=request.user)
        else:
            raise ValidationError({"workspace": "Must be owner or tenant."})
        return _paginate(
            request,
            queryset.select_related("property__owner", "tenant"),
            RentalInterestSerializer,
        )

    require_verified_rental_account(request.user)
    serializer = RentalInterestBodySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    property_obj = get_object_or_404(
        Property.objects.select_related("owner"), id=data["property_id"]
    )
    if property_obj.owner_id == request.user.pk:
        raise ValidationError("An owner cannot submit interest in their own property.")
    operation = "rental_interest.create"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        property_obj = Property.objects.select_for_update().get(pk=property_obj.pk)
        replay = _replay_response(
            request.user, operation, data["request_key"], request.data
        )
        if replay:
            return replay
        blocker = interest_creation_blocker(request.user, property_obj)
        if blocker:
            raise PermissionDenied(blocker)
        offer_id, snapshot = resolve_offer_snapshot(
            property_obj, data["offer_id"], data["offer_revision"], request
        )
        if snapshot.get("terms", {}).get("price_period") != "monthly":
            raise ValidationError({"offer_id": "V1 supports monthly offers only."})
        validate_interest_capacity(snapshot, data["occupants"])
        if data["desired_start"] < timezone.localdate():
            raise ValidationError({"desired_start": "Cannot be in the past."})
        interest = RentalInterest.objects.create(
            property=property_obj,
            tenant=request.user,
            offer_id=offer_id,
            offer_revision=data["offer_revision"],
            offer_snapshot=snapshot,
            desired_start=data["desired_start"],
            months=data["months"],
            occupants=data["occupants"],
            message=data.get("message", ""),
        )
        resource = RentalInterestSerializer(interest, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=property_obj.id,
            result_subject_id=interest.id,
            result_revision=interest.revision,
            resource=resource,
            response_status=201,
        )
        transaction.on_commit(
            lambda: _notify(
                property_obj.owner,
                Notification.NotificationType.RENTAL_INTEREST,
                "New rental interest",
                "open_rental_interest",
                interest.id,
                rental_interest_id=interest.id,
                workspace="owner",
            )
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_interest_detail(request, interest_id):
    interest = _participant_interest(request, interest_id)
    return Response(
        RentalInterestSerializer(interest, context={"request": request}).data
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_interest_respond(request, interest_id):
    _participant_interest(request, interest_id, provider_required=False)
    serializer = RentalDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    operation = f"rental_interest.respond.{interest_id}"
    replay = _replay_response(
        request.user, operation, data["request_key"], request.data
    )
    if replay:
        return replay
    with transaction.atomic():
        interest = _participant_interest(
            request, interest_id, lock=True, provider_required=False
        )
        replay = _replay_response(
            request.user, operation, data["request_key"], request.data
        )
        if replay:
            return replay
        if data["expected_revision"] != interest.revision:
            raise RentalConflict("Interest revision conflict.", code="stale_revision")
        decision = data["decision"]
        if decision not in interest_actions(request.user, interest):
            raise PermissionDenied("This decision is not allowed for the current interest.")
        if decision == "reject" and request.user == interest.property.owner:
            interest.status = RentalInterest.Status.REJECTED
        elif decision == "withdraw" and request.user == interest.tenant:
            interest.status = RentalInterest.Status.WITHDRAWN
        else:
            raise PermissionDenied(
                "This decision is not allowed for the current actor."
            )
        interest.revision += 1
        interest.save(update_fields=["status", "revision", "updated_at"])
        resource = RentalInterestSerializer(interest, context={"request": request}).data
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=data["request_key"],
            payload=request.data,
            request_subject_id=interest.id,
            result_subject_id=interest.id,
            result_revision=interest.revision,
            resource=resource,
        )
    return Response(output)
