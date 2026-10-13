"""Views: owner advertisement collection."""

from django.core.paginator import EmptyPage, Paginator
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from ..models import Advertisement, AdvertisingPlan
from ..renderers import AdvertisingJsonRenderer
from ..serializers import AdvertisementCreateSerializer
from ..services import (
    AdvertisingServiceError,
    create_advertisement,
    effective_status,
    plan_payload,
    record_rejected_operation,
)
from .language import (
    language,
    message,
    envelope,
    error_response,
    validation_error_response,
    finalize,
    iso8601,
)


def banner_url(request, advertisement):
    return request.build_absolute_uri(
        reverse("advertising:advertisement-media", args=[advertisement.id])
    )


def payment_payload(payment):
    if not payment:
        return None
    return {
        "id": str(payment.id),
        "advertisement_id": str(payment.advertisement.id),
        "operation_id": payment.operation_id,
        "payment_mode": payment.payment_mode,
        "status": payment.status,
    }


def advertisement_payload(request, advertisement, *, public=False, now=None):
    data = {
        "id": str(advertisement.id),
        "title": advertisement.title,
        "description": advertisement.description,
        "banner_url": banner_url(request, advertisement),
        "property_id": (
            str(advertisement.property.id) if advertisement.property_id else None
        ),
        "offer_id": advertisement.offer_id or None,
        "status": effective_status(advertisement, now),
        "starts_at": iso8601(advertisement.starts_at),
        "ends_at": iso8601(advertisement.ends_at),
    }
    if not public:
        data.update(
            {
                "operation_id": advertisement.operation.operation_id,
                "plan_snapshot": advertisement.plan_snapshot,
                "payment": payment_payload(getattr(advertisement, "payment", None)),
            }
        )
    return data


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
@renderer_classes([AdvertisingJsonRenderer])
def plan_list(request):
    plans = AdvertisingPlan.objects.filter(active=True).order_by("sort_order", "id")
    response = envelope(
        {"results": [plan_payload(plan, language(request)) for plan in plans]},
        message(request, "plans"),
    )
    return finalize(response, request, public_ttl=300)


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@renderer_classes([AdvertisingJsonRenderer])
def owner_advertisement_collection(request):
    if request.method == "GET":
        queryset = (
            Advertisement.objects.filter(owner=request.user)
            .select_related("operation", "payment", "property__owner")
            .order_by("-created_at", "-id")
        )
        try:
            page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 100)
            page_number = max(int(request.query_params.get("page", 1)), 1)
        except (TypeError, ValueError):
            page_size, page_number = 20, 1
        paginator = Paginator(queryset, page_size)
        try:
            page = paginator.page(page_number)
        except EmptyPage:
            page = []
        payload = {
            "count": paginator.count,
            "page": page_number,
            "per_page": page_size,
            "total_pages": paginator.num_pages,
            "next": page_number + 1 if page_number < paginator.num_pages else None,
            "previous": page_number - 1 if page_number > 1 else None,
            "results": [advertisement_payload(request, item) for item in page],
        }
        return finalize(
            envelope(payload, message(request, "owners")), request, private=True
        )

    serializer = AdvertisementCreateSerializer(data=request.data)
    if not serializer.is_valid():
        record_rejected_operation(
            request.user, request.data.get("operation_id"), serializer.errors
        )
        return finalize(
            validation_error_response(serializer, request), request, private=True
        )
    try:
        advertisement, created = create_advertisement(
            request.user, serializer.validated_data, language(request)
        )
    except AdvertisingServiceError as error:
        if error.errors not in (
            {"operation_id": ["idempotency_conflict"]},
            {"operation_id": ["operation_processing"]},
        ):
            record_rejected_operation(
                request.user, serializer.validated_data["operation_id"], error.errors
            )
        return finalize(error_response(error, request), request, private=True)
    advertisement = Advertisement.objects.select_related(
        "operation", "payment", "property__owner"
    ).get(pk=advertisement.pk)
    response = envelope(
        advertisement_payload(request, advertisement),
        message(request, "created"),
        status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )
    return finalize(response, request, private=True)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
@renderer_classes([AdvertisingJsonRenderer])
def owner_advertisement_detail(request, advertisement_id):
    advertisement = get_object_or_404(
        Advertisement.objects.select_related("operation", "payment", "property__owner"),
        id=advertisement_id,
        owner=request.user,
    )
    return finalize(
        envelope(
            advertisement_payload(request, advertisement), message(request, "detail")
        ),
        request,
        private=True,
    )
