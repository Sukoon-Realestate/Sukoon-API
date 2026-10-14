"""Property: property list apiview."""

from django.db.models import Count, Exists, OuterRef
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.features.models import BoostCampaign
from ...filters import PropertyFilter
from ...models import Property, PropertyVisit
from ...serializers import PropertyListSerializer, PropertyNewListSerializer
from .property_filter_options_apiview import PropertyPagination


class PropertyListAPIView(generics.ListAPIView):
    """
    API view to list properties.

    The paginated response includes a `banner` key with the authenticated
    tenant's next confirmed upcoming visit, if any.
    """

    queryset = (
        Property.objects.exclude(status=Property.Status.HIDDEN)
        .select_related("property_type", "governorate", "city")
        .annotate(images_count=Count("images"))
        .annotate(
            is_sponsored=Exists(
                BoostCampaign.objects.filter(
                    property=OuterRef("pkid"),
                    status=BoostCampaign.Status.ACTIVE,
                    starts_at__lte=timezone.now(),
                    ends_at__gt=timezone.now(),
                )
            )
        )
        .order_by("-created_at")
    )
    serializer_class = PropertyListSerializer
    renderer_classes = [GenericJsonRenderer]
    pagination_class = PropertyPagination
    permission_classes = [permissions.AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PropertyFilter
    search_fields = [
        "title",
        "description",
        "city__name",
        "governorate__name",
        "district",
    ]
    ordering_fields = ["price", "created_at"]

    def _get_upcoming_visit_banner(self):
        # ? Promote an approved upcoming visit to the top of the feed.
        user = self.request.user
        if not user.is_authenticated:
            return None

        today = timezone.localdate()
        visit = (
            PropertyVisit.objects.filter(
                tenant=user,
                status=PropertyVisit.Status.CONFIRMED,
                visit_date__gte=today,
            )
            .select_related("property")
            .order_by("visit_date", "visit_time")
            .first()
        )
        if not visit:
            return None

        return {
            "visit_id": str(visit.id),
            "property_id": str(visit.property.id),
            "property_title": visit.property.title,
            "property_district": visit.property.district,
            "visit_date": visit.visit_date.isoformat(),
            "visit_time": visit.visit_time.strftime("%H:%M"),
            "is_today": visit.visit_date == today,
        }

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            # ! Mutate the paginated payload before rendering; DRF Response.data
            # ! is the unrendered dict, so this is safe.
            response.data["banner"] = self._get_upcoming_visit_banner()
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "banner": self._get_upcoming_visit_banner(),
                "results": serializer.data,
            }
        )


class PropertyNewListAPIView(generics.ListAPIView):
    """
    API view to list the newest property listings in card format.

    Returns a compact payload for the property card UI: image gallery count,
    verification badge, title, location, bedrooms, bathrooms, area, tags,
    price and price period.

    Supports the same filtering, search and ordering options as the main
    property list endpoint.

    Filters:
    - property_type (e.g. ?property_type=apartment)
    - price_period, is_furnished, is_verified, bedrooms, bathrooms
    - suitable_for, smoking_allowed, has_wifi, has_elevator, has_garage
    - has_security, has_balcony, has_air_conditioning, near_metro
    - has_natural_gas, price_min, price_max

    Search:
    - ?search=nasr (searches title, description, city, district)

    Ordering:
    - ?ordering=price or ?ordering=-created_at
    """

    queryset = (
        Property.objects.exclude(status=Property.Status.HIDDEN)
        .select_related("property_type", "governorate", "city")
        .annotate(images_count=Count("images"))
        .annotate(
            is_sponsored=Exists(
                BoostCampaign.objects.filter(
                    property=OuterRef("pkid"),
                    status=BoostCampaign.Status.ACTIVE,
                    starts_at__lte=timezone.now(),
                    ends_at__gt=timezone.now(),
                )
            )
        )
        .order_by("-created_at")
    )
    serializer_class = PropertyNewListSerializer
    renderer_classes = [GenericJsonRenderer]
    pagination_class = PropertyPagination
    permission_classes = [permissions.AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PropertyFilter
    search_fields = [
        "title",
        "description",
        "city__name",
        "governorate__name",
        "district",
    ]
    ordering_fields = ["price", "created_at"]
