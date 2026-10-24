"""Rental phase2 views: rental interests."""

from datetime import timedelta
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
        # Pair decisions live in the shared plan until independent invitations exist.
        from django.db.models import Q
        queryset = queryset.filter(Q(shared_allocation__isnull=True) | Q(shared_allocation__proposal__plan__status="handed_off"))
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
        from ..services.student_housing.applications import context

        academic = context(request.user, data)
        property_obj = Property.objects.select_for_update().get(pk=property_obj.pk)
        replay = _replay_response(
            request.user, operation, data["request_key"], request.data
        )
        if replay:
            return replay
        from core_apps.chat.moderation.policy import require_new_business
        require_new_business(request.user)
        require_new_business(property_obj.owner)
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
        desired_end = data.get("desired_end")
        if desired_end:
            from ..services.rental_phase2 import add_months

            minimum = max(1, int(snapshot["terms"].get("rental_period") or 1))
            if desired_end < add_months(
                data["desired_start"], minimum
            ) or desired_end > add_months(data["desired_start"], 60):
                raise ValidationError(
                    {
                        "desired_end": "Review the minimum monthly term and requested end date."
                    }
                )
            months = (
                (desired_end.year - data["desired_start"].year) * 12
                + desired_end.month
                - data["desired_start"].month
            )
            if add_months(data["desired_start"], months) > desired_end:
                months -= 1
            if data["months"] != months:
                raise ValidationError(
                    {
                        "months": "Use the whole calendar months within the requested dates."
                    }
                )
            if academic and desired_end != academic["desired_end"]:
                raise ValidationError(
                    {"desired_end": "Use the reviewed academic dates."}
                )
            if not academic:
                academic["desired_end"] = desired_end
        from ..services.rental_lifecycle.applications import valid_interest_share

        grant = (
            valid_interest_share(
                data["application_share_id"], request.user, property_obj
            )
            if data.get("application_share_id")
            else None
        )
        from ..services.rental_application_records import create_interest

        interest = create_interest(
            **academic,
            application_grant=grant,
            response_due_at=timezone.now() + timedelta(hours=48),
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
        from ..services.rental_lifecycle.notifications import record_rental_event

        record_rental_event(
            interest,
            {property_obj.owner},
            "application.submitted",
            "open_rental_interest",
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
            raise PermissionDenied(
                "This decision is not allowed for the current interest."
            )
        if decision == "reject" and request.user == interest.property.owner:
            interest.status = RentalInterest.Status.REJECTED
            interest.waiting_for = ""
        elif decision == "withdraw" and request.user == interest.tenant:
            interest.status = RentalInterest.Status.WITHDRAWN
            interest.waiting_for = ""
        elif (
            decision == "request_information"
            and request.user == interest.property.owner
        ):
            if not data.get("note", "").strip():
                raise ValidationError({"note": "Describe the missing information."})
            interest.information_requested = data["note"].strip()
            interest.applicant_response = ""
            interest.waiting_for = "tenant"
            interest.status = RentalInterest.Status.UNDER_REVIEW
        elif decision == "provide_information" and request.user == interest.tenant:
            if not data.get("note", "").strip():
                raise ValidationError({"note": "Provide the requested information."})
            interest.applicant_response = data["note"].strip()
            interest.waiting_for = "owner"
        elif (
            decision == "mark_under_review" and request.user == interest.property.owner
        ):
            interest.status = RentalInterest.Status.UNDER_REVIEW
            interest.waiting_for = "owner"
        else:
            raise PermissionDenied(
                "This decision is not allowed for the current actor."
            )
        if (
            request.user == interest.property.owner
            and not interest.first_owner_response_at
        ):
            interest.first_owner_response_at = timezone.now()
        interest.response_due_at = (
            timezone.now() + timedelta(hours=48) if interest.waiting_for else None
        )
        interest.revision += 1
        interest.save()
        from ..services.rental_lifecycle.common import audit
        from ..services.rental_lifecycle.notifications import record_rental_event

        audit(interest, request.user, f"application.{decision}", data.get("note", ""))
        recipient = (
            interest.tenant
            if request.user == interest.property.owner
            else interest.property.owner
        )
        record_rental_event(
            interest, {recipient}, f"application.{decision}", "open_rental_interest"
        )
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
