from django.core.paginator import EmptyPage, Paginator
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from datetime import timezone as datetime_timezone

from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import Advertisement, AdvertisementOperation, AdvertisingPlan
from .renderers import AdvertisingJsonRenderer
from .serializers import AdvertisementCreateSerializer, MockPaymentSerializer
from .services import (
    AdvertisingServiceError,
    activate_with_mock_payment,
    create_advertisement,
    destination_is_eligible,
    effective_status,
    plan_payload,
    record_rejected_operation,
)


MESSAGES = {
    "plans": {"en": "Available plans.", "ar": "الخطط المتاحة."},
    "created": {
        "en": "Advertisement created, awaiting simulated payment.",
        "ar": "تم إنشاء الإعلان وهو بانتظار الدفع التجريبي.",
    },
    "owners": {"en": "Owner advertisements.", "ar": "إعلانات المالك."},
    "detail": {"en": "Advertisement details.", "ar": "تفاصيل الإعلان."},
    "paid": {
        "en": "Simulated payment succeeded. No money collected.",
        "ar": "نجح الدفع التجريبي. لم يتم تحصيل أي أموال.",
    },
    "active": {"en": "Active advertisements.", "ar": "الإعلانات النشطة."},
    "found": {"en": "Operation found.", "ar": "تم العثور على العملية."},
    "processing": {
        "en": "Operation is still processing.",
        "ar": "ما زالت العملية قيد التنفيذ.",
    },
    "not_found": {
        "en": "No committed advertisement. Retry is safe.",
        "ar": "لا يوجد إعلان مثبت. إعادة المحاولة آمنة.",
    },
    "rejected": {
        "en": "Rejected before creation. Correct the input.",
        "ar": "رُفض الطلب قبل الإنشاء. صحح البيانات.",
    },
}

ERROR_MESSAGES_AR = {
    "Please correct the invalid fields.": "يرجى تصحيح الحقول غير الصالحة.",
    "The banner must not exceed 10 MiB.": "يجب ألا يتجاوز حجم البانر 10 ميبيبايت.",
    "The banner is not a valid supported image.": "ملف البانر ليس صورة صالحة ومدعومة.",
    "Only JPEG, PNG, and WebP banners are supported.": "تُدعم صور JPEG وPNG وWebP فقط.",
    "The selected property is not eligible for publication.": "العقار المحدد غير مؤهل للنشر.",
    "The selected offer is not eligible for publication.": "العرض المحدد غير مؤهل للنشر.",
    "This operation ID was already used with different data.": "استُخدم معرف العملية هذا سابقًا ببيانات مختلفة.",
    "This operation is still processing.": "ما زالت هذه العملية قيد التنفيذ.",
    "This operation is already being processed.": "هذه العملية قيد التنفيذ بالفعل.",
    "The selected plan is unavailable.": "الخطة المحددة غير متاحة.",
    "The selected plan changed. Review the current plan before continuing.": (
        "تغيرت الخطة المحددة. راجع الخطة الحالية قبل المتابعة."
    ),
    "Advertisement not found.": "الإعلان غير موجود.",
    "This account is not eligible to publish advertisements.": "هذا الحساب غير مؤهل لنشر الإعلانات.",
    "This advertisement cannot be activated from its current state.": "لا يمكن تفعيل هذا الإعلان من حالته الحالية.",
    "The payment operation ID does not match this advertisement.": "معرف عملية الدفع لا يطابق هذا الإعلان.",
    "Only simulated payment is available.": "الدفع التجريبي هو الوضع المتاح فقط.",
    "The advertisement destination is no longer eligible.": "وجهة الإعلان لم تعد مؤهلة.",
    "The advertisement media is unavailable.": "وسائط الإعلان غير متاحة.",
}


def language(request):
    return (
        "ar" if str(getattr(request, "LANGUAGE_CODE", "en")).startswith("ar") else "en"
    )


def message(request, key):
    return MESSAGES[key][language(request)]


def envelope(data, text, *, status_code=200):
    return Response(
        {"key": "success", "message": text, "data": data}, status=status_code
    )


def error_response(error, request=None):
    text = error.message
    if request is not None and language(request) == "ar":
        text = ERROR_MESSAGES_AR.get(text, text)
    return Response(
        {
            "key": "error",
            "message": text,
            "data": None,
            "errors": error.errors,
        },
        status=error.status_code,
    )


def validation_error_response(serializer, request):
    return Response(
        {
            "key": "error",
            "message": (
                ERROR_MESSAGES_AR["Please correct the invalid fields."]
                if language(request) == "ar"
                else "Please correct the invalid fields."
            ),
            "data": None,
            "errors": serializer.errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def finalize(response, request, *, private=False, public_ttl=None):
    response["Content-Language"] = language(request)
    response["Vary"] = "Accept-Language"
    if private:
        response["Cache-Control"] = "no-store"
    elif public_ttl is not None:
        response["Cache-Control"] = (
            f"public, max-age={max(0, int(public_ttl))}, must-revalidate"
        )
    return response


def iso8601(value):
    if value is None:
        return None
    value = value.astimezone(datetime_timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def banner_url(request, advertisement):
    return request.build_absolute_uri(
        reverse("advertising:advertisement-media", args=[advertisement.id])
    )


def payment_payload(payment):
    if not payment:
        return None
    return {
        "id": str(payment.id),
        "advertisement_id": str(payment.advertisement_id),
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
            str(advertisement.property_id) if advertisement.property_id else None
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
        .select_related("property__owner", "operation", "payment")
        .order_by("-starts_at", "-id")
    )
    results = []
    nearest_end = None
    for advertisement in candidates.iterator():
        if not destination_is_eligible(advertisement):
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
        Advertisement.objects.select_related("media", "property__owner"),
        id=advertisement_id,
        media__isnull=False,
    )
    is_public = (
        effective_status(advertisement) == Advertisement.Status.ACTIVE
        and destination_is_eligible(advertisement)
        and advertisement.owner.is_active
        and getattr(getattr(advertisement, "payment", None), "status", None)
        == "mock_succeeded"
    )
    if not is_public and (
        not request.user.is_authenticated or request.user != advertisement.owner
    ):
        return finalize(
            error_response(
                AdvertisingServiceError("Advertisement not found.", status_code=404),
                request,
            ),
            request,
            private=True,
        )
    response = FileResponse(
        advertisement.media.banner.open("rb"),
        content_type=advertisement.media.content_type,
    )
    response["Content-Disposition"] = "inline"
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = (
        "public, max-age=60, must-revalidate" if is_public else "no-store"
    )
    return response
