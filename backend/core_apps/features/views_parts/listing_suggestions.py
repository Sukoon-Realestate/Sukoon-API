"""Views: listing suggestions."""

from datetime import timedelta
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.common.models import ContentView
from core_apps.properties.models import Property, PropertyVisit, SavedProperty
from ..models import ListingSuggestion
from ..renderers import FeatureJsonRenderer
from .rental_operation_lookup import _replay, _remember


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def owner_analytics(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    language = request.query_params.get("lang") or request.headers.get(
        "Accept-Language", "en"
    )
    is_arabic = language.lower().startswith("ar")
    try:
        period_days = int(request.query_params.get("period_days", 30))
    except ValueError:
        raise ValidationError({"period_days": "Must be 7, 30, or 90."})
    if period_days not in {7, 30, 90}:
        raise ValidationError({"period_days": "Must be 7, 30, or 90."})
    since = timezone.now() - timedelta(days=period_days)
    ct = ContentType.objects.get_for_model(Property)
    views = ContentView.objects.filter(
        content_type=ct, object_id=property_obj.pkid, last_viewed__gte=since
    ).count()
    visits = PropertyVisit.objects.filter(
        property=property_obj, created_at__gte=since
    ).count()
    conversion = round((visits / views) * 100, 2) if views else None
    saved = SavedProperty.objects.filter(
        property=property_obj, created_at__gte=since
    ).count()
    return Response(
        {
            "property_id": str(property_obj.id),
            "period_days": period_days,
            "measured_at": timezone.now().isoformat(),
            "methodology": (
                "مشاهدات العقار الفريدة المسجلة وطلبات المعاينة خلال فترة التقرير المحددة بتوقيت القاهرة."
                if is_arabic
                else "Unique stored property views and created visit requests in the "
                "selected Africa/Cairo reporting window."
            ),
            "metrics": [
                {
                    "key": "unique_views",
                    "label": "الزوار الفريدون" if is_arabic else "Unique visitors",
                    "value": views,
                    "unit": "count",
                    "definition": (
                        "سجلات مشاهدات العقار المميزة خلال الفترة المحددة."
                        if is_arabic
                        else "Stored distinct property view records in the period."
                    ),
                },
                {
                    "key": "viewing_conversion",
                    "label": (
                        "معدل طلب المعاينة" if is_arabic else "Viewing request rate"
                    ),
                    "value": conversion,
                    "unit": "percent",
                    "definition": (
                        "عدد طلبات المعاينة خلال الفترة مقسومًا على عدد المشاهدات الفريدة المسجلة."
                        if is_arabic
                        else "Visit requests created in the period divided by unique stored views."
                    ),
                },
                {
                    "key": "saved_count",
                    "label": "مرات الحفظ" if is_arabic else "Saves",
                    "value": saved,
                    "unit": "count",
                    "definition": (
                        "مرات حفظ العقار الجديدة خلال الفترة المحددة."
                        if is_arabic
                        else "New saves in the period."
                    ),
                },
            ],
            "export_url": "",
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def listing_suggestions(request):
    required = {"facts", "language", "request_key"}
    if not required.issubset(request.data):
        raise ValidationError(
            {key: "This field is required." for key in required - set(request.data)}
        )
    if request.data["language"] not in {"ar", "en"} or not isinstance(
        request.data["facts"], dict
    ):
        raise ValidationError("language must be ar/en and facts must be an object.")
    replay = _replay(
        request.user, "suggestion.create", request.data["request_key"], request.data
    )
    if replay:
        return replay
    property_obj = None
    if request.data.get("property_id"):
        property_obj = get_object_or_404(
            Property, id=request.data["property_id"], owner=request.user
        )
    facts = request.data["facts"]
    title = str(
        facts.get("title")
        or ("مسكن مميز" if request.data["language"] == "ar" else "A distinctive home")
    )[:150]
    description = str(facts.get("description") or "").strip()
    if not description:
        place = facts.get("district") or facts.get("governorate") or ""
        description = (
            f"مسكن متاح في {place}"
            if request.data["language"] == "ar"
            else f"A home available in {place}"
        ).strip()
    warnings = (
        []
        if facts.get("description")
        else ["Description was generated only from the supplied public facts."]
    )
    with transaction.atomic():
        suggestion = ListingSuggestion.objects.create(
            owner=request.user,
            property=property_obj,
            language=request.data["language"],
            facts=facts,
            suggested_title=title,
            suggested_description=description[:5000],
            warnings=warnings,
        )
        data = {
            "id": str(suggestion.id),
            "property_id": str(property_obj.id) if property_obj else "",
            "suggested_title": suggestion.suggested_title,
            "suggested_description": suggestion.suggested_description,
            "warnings": warnings,
        }
        _remember(
            request.user,
            "suggestion.create",
            request.data["request_key"],
            request.data,
            data,
            201,
        )
    return Response(data, status=status.HTTP_201_CREATED)
