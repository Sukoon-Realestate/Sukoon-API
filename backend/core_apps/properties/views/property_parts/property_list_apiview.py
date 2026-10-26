from core_apps.properties.search import PropertySearchFilter

"""Property: property list apiview."""

from django.db.models import Count, Exists, OuterRef
from django.db.models.functions import Now
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions
from rest_framework.response import Response
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.features.models import BoostCampaign
from ...filters import PropertyFilter, PropertyOrderingFilter
from ...models import Property
from ...serializers import PropertyListSerializer, PropertyNewListSerializer
from .property_filter_options_apiview import PropertyPagination


class VisiblePropertyListMixin:
    def get_queryset(self):
        from ...services.public_access import public_properties

        return public_properties(super().get_queryset())


class PropertyListAPIView(VisiblePropertyListMixin, generics.ListAPIView):
    """
    API view to list properties.

    The paginated response includes a `banner` key with the authenticated
    tenant's next confirmed upcoming visit, if any.
    """

    queryset = (
        Property.objects.filter(
            status=Property.Status.VERIFIED, retired_at__isnull=True
        )
        .select_related("property_type", "governorate", "city")
        .annotate(images_count=Count("images"))
        .annotate(
            is_sponsored=Exists(
                BoostCampaign.objects.filter(
                    property=OuterRef("pkid"),
                    status=BoostCampaign.Status.ACTIVE,
                    starts_at__lte=Now(),
                    ends_at__gt=Now(),
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
        PropertySearchFilter,
        PropertyOrderingFilter,
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
        return None

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            # ! Mutate the paginated payload before rendering; DRF Response.data
            # ! is the unrendered dict, so this is safe.
            response.data["banner"] = self._get_upcoming_visit_banner()
            if hasattr(request, "student_offer_matches"):
                response.data["student_search_version"] = 1
            if getattr(request, "rental_search_version", None):
                response.data["rental_search_version"] = 1
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "banner": self._get_upcoming_visit_banner(),
                "results": serializer.data,
            }
        )


class PropertyNewListAPIView(VisiblePropertyListMixin, generics.ListAPIView):
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
        Property.objects.filter(
            status=Property.Status.VERIFIED, retired_at__isnull=True
        )
        .select_related("property_type", "governorate", "city")
        .annotate(images_count=Count("images"))
        .annotate(
            is_sponsored=Exists(
                BoostCampaign.objects.filter(
                    property=OuterRef("pkid"),
                    status=BoostCampaign.Status.ACTIVE,
                    starts_at__lte=Now(),
                    ends_at__gt=Now(),
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
        PropertySearchFilter,
        PropertyOrderingFilter,
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

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if hasattr(request, "student_offer_matches") and isinstance(
            response.data, dict
        ):
            response.data["student_search_version"] = 1
            if getattr(request, "rental_search_version", None):
                response.data["rental_search_version"] = 1
        return response
