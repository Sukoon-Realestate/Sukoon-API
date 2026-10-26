"""Property: property filter options apiview."""

import logging
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.response import Response
from core_apps.common.pagination import StandardResultsSetPagination
from core_apps.common.renderers import GenericJsonRenderer
from ...models import Property, PropertyType
from ...serializers import AvailablePlacesQuerySerializer, PropertyTypeSerializer
from ...services import PropertyService


logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def confirm_property_availability(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    property_obj.availability_confirmed_at = timezone.now()
    property_obj.save(update_fields=["availability_confirmed_at", "updated_at"])
    return Response(
        {
            "id": str(property_obj.id),
            "availability_confirmed_at": property_obj.availability_confirmed_at.isoformat(),
            "status": "confirmed",
        }
    )


def get_client_ip(request):
    # ? Behind a proxy the real client IP is the first entry of X-Forwarded-For
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class PropertyPagination(StandardResultsSetPagination):
    page_size = 9
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        """Expose the exact filtered count needed by the filter action button."""
        response = super().get_paginated_response(data)
        response.data["count"] = self.page.paginator.count
        return response


class PropertyTypeListAPIView(generics.ListAPIView):
    """
    API view to list available property types (managed by admins).

    Returns active property types with stable IDs and current catalog revisions.
    """

    queryset = PropertyType.objects.filter(is_active=True)
    pagination_class = None
    serializer_class = PropertyTypeSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        # This is a selector catalog. Return all active choices in its existing
        # results envelope, as filter-options already does, without hiding page 2.
        values = self.get_serializer(self.get_queryset(), many=True).data
        return Response(
            {"count": len(values), "next": None, "previous": None, "results": values}
        )


class PropertyFilterOptionsAPIView(generics.GenericAPIView):
    """Return all option values accepted by the property listing filters."""

    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        from core_apps.common.locale_middleware import resolve_request_language

        return Response(
            PropertyService.get_filter_options(resolve_request_language(request))
        )


class AvailablePlacesAPIView(generics.GenericAPIView):
    """Return distinct locations with approved properties of the requested type."""

    serializer_class = AvailablePlacesQuerySerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        places = PropertyService.get_available_places(
            serializer.validated_data["property_type"]
        )
        return Response({"places": places})
