"""Visit: property visit create apiview."""

import logging
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from core_apps.common.idempotency import (
    execute_idempotent,
    request_key as get_idempotency_key,
    response_headers,
)
from core_apps.common.pagination import StandardResultsSetPagination
from core_apps.common.renderers import GenericJsonRenderer
from ...models import Property
from ...serializers import (
    PropertyVisitCreateSerializer,
    TenantVisitRequestDetailSerializer,
)
from ...serializers.visit import get_visit_language
from ...services import PropertyVisitService


logger = logging.getLogger(__name__)


class PropertyVisitPagination(StandardResultsSetPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class PropertyVisitCreateAPIView(generics.CreateAPIView):
    """
    API view for a tenant to request/book a visit for a property.

    Request Body Example:
    {
        "visit_date": "2026-07-20",
        "visit_time": "14:00:00",
        "note": "Looking forward to seeing the apartment."
    }
    """

    serializer_class = PropertyVisitCreateSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        property_obj = get_object_or_404(
            Property.objects.all(), id=self.kwargs["property_id"]
        )
        serializer.save(tenant=self.request.user, property_obj=property_obj)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Recheck authority even when the original command has a receipt.
        from ...services.viewing_access import prepare_context

        prepare_context(
            request.user, serializer.validated_data.get("viewing_context", {})
        )
        property_obj = get_object_or_404(
            Property.objects.select_related(
                "owner", "owner__profile", "property_type", "governorate", "city"
            ),
            id=self.kwargs["property_id"],
        )
        request_key = get_idempotency_key(request)

        def create_visit():
            visit = serializer.save(tenant=request.user, property_obj=property_obj)
            response_data = TenantVisitRequestDetailSerializer(
                visit, context={"request": request}
            ).data
            return (
                {"message": "Visit request submitted successfully.", **response_data},
                status.HTTP_201_CREATED,
                visit.id,
            )

        data, response_status, replayed = execute_idempotent(
            user=request.user,
            operation=f"property.visit.create:{property_obj.id}",
            key=request_key,
            payload=serializer.validated_data,
            action=create_visit,
            request_subject_id=property_obj.id,
        )
        return Response(
            data,
            status=response_status,
            headers=response_headers(replayed),
        )
