"""Views: boost campaigns."""

from ..catalog_models import PromotionOption
from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.properties.models import Property
from ..models import BoostCampaign, SearchAlert
from ..renderers import FeatureJsonRenderer
from ..serializers import (
    AlertCreateSerializer,
    BoostCampaignSerializer,
    RevisionRequestSerializer,
    SearchAlertSerializer,
)
from .rental_operation_lookup import _replay, _remember, _paginate


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
@transaction.atomic
def boost_campaigns(request):
    if request.method == "GET":
        return _paginate(
            request,
            BoostCampaign.objects.filter(owner=request.user).select_related("property"),
            BoostCampaignSerializer,
        )
    required = {"property_id", "option_id", "request_key"}
    if not required.issubset(request.data):
        raise ValidationError(
            {key: "This field is required." for key in required - set(request.data)}
        )
    property_obj = get_object_or_404(
        Property.objects.select_for_update(),
        id=request.data["property_id"],
        owner=request.user,
    )
    replay = _replay(
        request.user, "boost.create", request.data["request_key"], request.data
    )
    if replay:
        return replay
    option = PromotionOption.objects.filter(
        id=request.data["option_id"], active=True
    ).first()
    if not option:
        raise ValidationError({"option_id": "Unsupported promotion option."})
    property_obj = get_object_or_404(
        Property, id=request.data["property_id"], owner=request.user
    )
    if property_obj.status != Property.Status.VERIFIED or not property_obj.is_verified:
        raise ValidationError("Only published, verified properties can be promoted.")
    now = timezone.now()
    if BoostCampaign.objects.filter(
        property=property_obj, status__in=["pending", "active"], ends_at__gt=now
    ).exists():
        raise ValidationError("This property already has an active campaign.")
    with transaction.atomic():
        campaign = BoostCampaign.objects.create(
            owner=request.user,
            property=property_obj,
            option_id=request.data["option_id"],
            duration_days=option.duration_days,
            starts_at=now,
            ends_at=now + timedelta(days=option.duration_days),
            status=BoostCampaign.Status.ACTIVE,
        )
        data = {
            "id": str(campaign.id),
            "subject_id": str(property_obj.id),
            "status": campaign.status,
            "message": "Promotion activated.",
        }
        _remember(
            request.user,
            "boost.create",
            request.data["request_key"],
            request.data,
            data,
            201,
        )
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
@transaction.atomic
def search_alerts(request):
    if request.method == "GET":
        return _paginate(
            request,
            SearchAlert.objects.filter(user=request.user, deleted_at__isnull=True),
            SearchAlertSerializer,
        )
    serializer = AlertCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data
    from django.contrib.auth import get_user_model

    get_user_model().objects.select_for_update().get(pk=request.user.pk)
    replay = _replay(request.user, "alert.create", payload["request_key"], request.data)
    if replay:
        return replay
    with transaction.atomic():
        alert = SearchAlert.objects.create(
            user=request.user,
            name=payload["name"],
            cadence=payload["cadence"],
            filters=payload["filters"],
        )
        data = {"id": str(alert.id), "subject_id": str(alert.id), "status": "active"}
        _remember(
            request.user,
            "alert.create",
            payload["request_key"],
            request.data,
            data,
            201,
        )
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def search_alert_detail(request, alert_id):
    alert = get_object_or_404(SearchAlert, id=alert_id, user=request.user)
    if request.method == "GET":
        if alert.deleted_at:
            from rest_framework.exceptions import NotFound

            raise NotFound()
        return Response(SearchAlertSerializer(alert, context={"request": request}).data)
    serializer = RevisionRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    operation = "alert.delete" if request.method == "DELETE" else "alert.update"
    with transaction.atomic():
        alert = SearchAlert.objects.select_for_update().get(pk=alert.pk)
        replay = _replay(
            request.user,
            operation,
            serializer.validated_data["request_key"],
            request.data,
        )
        if replay:
            return replay
        if alert.deleted_at:
            from rest_framework.exceptions import NotFound

            raise NotFound()
        if serializer.validated_data["revision"] != alert.revision:
            return Response(
                {"message": "Alert revision conflict."}, status=status.HTTP_409_CONFLICT
            )
        if request.method == "DELETE":
            alert.enabled = False
            alert.deleted_at = timezone.now()
            action_status = "cancelled"
        else:
            if "enabled" not in request.data or not isinstance(
                request.data["enabled"], bool
            ):
                raise ValidationError({"enabled": "A boolean is required."})
            alert.enabled = request.data["enabled"]
            action_status = "active" if alert.enabled else "paused"
        alert.revision += 1
        alert.save(update_fields=["enabled", "deleted_at", "revision", "updated_at"])
        data = {
            "id": str(alert.id),
            "subject_id": str(alert.id),
            "status": action_status,
            "revision": alert.revision,
        }
        _remember(
            request.user,
            operation,
            serializer.validated_data["request_key"],
            request.data,
            data,
            200,
        )
    return Response(data)
