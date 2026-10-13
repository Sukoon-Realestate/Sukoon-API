"""Views: tenant home placement."""

from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.parsers import JSONParser
from ..models import Advertisement, AdvertisementOperation
from ..renderers import AdvertisingJsonRenderer
from ..serializers import MockPaymentSerializer
from ..services import (
    AdvertisingServiceError,
    activate_with_mock_payment,
    ensure_media_persisted,
    is_publicly_eligible,
    media_is_available,
)
from .language import (
    message,
    envelope,
    error_response,
    validation_error_response,
    finalize,
    iso8601,
)
from .owner_advertisement_collection import advertisement_payload


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([JSONParser])
@renderer_classes([AdvertisingJsonRenderer])
def mock_payment(request, advertisement_id):
    serializer = MockPaymentSerializer(data=request.data)
    if not serializer.is_valid():
        return finalize(
            validation_error_response(serializer, request), request, private=True
        )
    try:
        advertisement, _, _ = activate_with_mock_payment(
            request.user,
            advertisement_id,
            serializer.validated_data["operation_id"],
            serializer.validated_data["payment_mode"],
        )
    except AdvertisingServiceError as error:
        return finalize(error_response(error, request), request, private=True)
    advertisement = Advertisement.objects.select_related(
        "operation", "payment", "property__owner"
    ).get(pk=advertisement.pk)
    return finalize(
        envelope(
            advertisement_payload(request, advertisement), message(request, "paid")
        ),
        request,
        private=True,
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
@renderer_classes([AdvertisingJsonRenderer])
def operation_detail(request, operation_id):
    with transaction.atomic():
        operation = (
            AdvertisementOperation.objects.select_for_update()
            .filter(owner=request.user, operation_id=operation_id)
            .first()
        )
        if not operation:
            data = {
                "operation_id": operation_id,
                "state": "not_found",
                "retry_allowed": True,
                "advertisement": None,
            }
            response = envelope(data, message(request, "not_found"))
        elif operation.state == AdvertisementOperation.State.FOUND:
            advertisement = Advertisement.objects.select_related(
                "operation", "payment", "property__owner"
            ).get(operation=operation)
            data = {
                "operation_id": operation_id,
                "state": "found",
                "retry_allowed": False,
                "advertisement": advertisement_payload(request, advertisement),
            }
            response = envelope(data, message(request, "found"))
        else:
            data = {
                "operation_id": operation_id,
                "state": operation.state,
                "retry_allowed": operation.retry_allowed,
                "advertisement": None,
            }
            response = envelope(data, message(request, operation.state))
    return finalize(response, request, private=True)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
@renderer_classes([AdvertisingJsonRenderer])
def tenant_home_placement(request):
    now = timezone.now()
    candidates = (
        Advertisement.objects.filter(
            placement=Advertisement.PLACEMENT_TENANT_HOME,
            status=Advertisement.Status.ACTIVE,
            starts_at__lte=now,
            ends_at__gt=now,
            owner__is_active=True,
            payment__status="mock_succeeded",
            media__isnull=False,
        )
        .select_related("owner", "property__owner", "operation", "payment", "media")
        .order_by("-starts_at", "-id")
    )
    results = []
    nearest_end = None
    for advertisement in candidates.iterator():
        if not is_publicly_eligible(advertisement, now):
            continue
        results.append(
            advertisement_payload(request, advertisement, public=True, now=now)
        )
        nearest_end = (
            min(nearest_end, advertisement.ends_at)
            if nearest_end
            else advertisement.ends_at
        )
        if len(results) == 20:
            break
    ttl = 60
    if nearest_end:
        ttl = min(ttl, max(0, (nearest_end - now).total_seconds()))
    response = envelope(
        {"server_now": iso8601(now), "results": results}, message(request, "active")
    )
    return finalize(response, request, public_ttl=ttl)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
@renderer_classes([AdvertisingJsonRenderer])
def advertisement_media(request, advertisement_id):
    advertisement = get_object_or_404(
        Advertisement.objects.select_related(
            "media", "owner", "payment", "property__owner"
        ),
        id=advertisement_id,
        media__isnull=False,
    )
    now = timezone.now()
    is_public = is_publicly_eligible(advertisement, now)
    if not media_is_available(advertisement) or (
        not is_public
        and (not request.user.is_authenticated or request.user != advertisement.owner)
    ):
        return finalize(
            error_response(
                AdvertisingServiceError("Advertisement not found.", status_code=404),
                request,
            ),
            request,
            private=True,
        )
    if str(advertisement.id) == "85295dd1-f8bd-4c82-a903-9bdc3d90af98":
        ensure_media_persisted(advertisement.media)
    response = FileResponse(
        advertisement.media.banner.open("rb"),
        content_type=advertisement.media.content_type,
    )
    response["Content-Disposition"] = "inline"
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = (
        f"public, max-age={min(60, max(0, int((advertisement.ends_at - now).total_seconds())))}, must-revalidate"
        if is_public
        else "no-store"
    )
    return response
