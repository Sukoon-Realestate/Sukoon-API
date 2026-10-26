"""Views: boost campaigns."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import BoostCampaign, SearchAlert
from ..renderers import FeatureJsonRenderer
from ..serializers import (
    AlertCreateSerializer,
    BoostCampaignSerializer,
    RevisionRequestSerializer,
    SearchAlertSerializer,
)
from .rental_operation_lookup import _replay, _remember, _paginate
from ..services.rental_foundation import private_no_store


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def boost_campaign_detail(request, campaign_id):
    campaign = get_object_or_404(
        BoostCampaign.objects.select_related("property"),
        id=campaign_id,
        owner=request.user,
    )
    return private_no_store(Response(BoostCampaignSerializer(campaign).data))


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
    from ..services.promotion_commands import create

    data, code = create(request.user, request.data)
    return Response(data, status=code)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def boost_campaign_resolve(request):
    from ..services.promotion_commands import resolve

    return private_no_store(Response(resolve(request.user, request.data)))


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
    if payload["cadence"] == "instant":
        from ..services.entitlements import enforce

        enforce(request.user, "priority_alerts", "tenant")
    with transaction.atomic():
        alert = SearchAlert.objects.create(
            user=request.user,
            name=payload["name"],
            cadence=payload["cadence"],
            filters=payload["filters"],
        )
        if alert.cadence == "instant":
            from ..models import CommerceFeature, FeatureUsage
            from ..services.rental_phase2 import fingerprint

            feature = CommerceFeature.objects.filter(code="priority_alerts").first()
            if feature:
                FeatureUsage.objects.create(
                    user=request.user,
                    feature=feature,
                    request_key=payload["request_key"],
                    resource_id=alert.id,
                    fingerprint=fingerprint(request.data),
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
        from django.contrib.auth import get_user_model

        get_user_model().objects.select_for_update().get(pk=request.user.pk)
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
            if (
                request.data["enabled"]
                and not alert.enabled
                and alert.cadence == "instant"
            ):
                from ..services.entitlements import enforce

                enforce(request.user, "priority_alerts", "tenant")
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
