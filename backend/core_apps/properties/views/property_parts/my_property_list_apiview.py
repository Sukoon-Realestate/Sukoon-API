"""Property: my property list apiview."""

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.db.models import Count, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from core_apps.common.models import ContentView
from core_apps.common.renderers import GenericJsonRenderer
from ...models import Property
from ...permissions import IsOwner, IsOwnerOrReadOnly
from ...serializers import (
    MyPropertyListSerializer,
    PropertyDetailSerializer,
    PropertySerializer,
)
from ...services import PropertyService
from .property_filter_options_apiview import PropertyPagination


class MyPropertyListAPIView(generics.ListAPIView):
    """
    API view for an owner to list their own properties with per-property stats:
    title, main image, price, moderation status, number of views and number of
    visit requests.
    """

    serializer_class = MyPropertyListSerializer
    renderer_classes = [GenericJsonRenderer]
    pagination_class = PropertyPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # ? ContentView uses a generic FK on the internal pkid, so a subquery is
        # ? needed to count views without a reverse relation
        property_content_type = ContentType.objects.get_for_model(Property)
        views_count_subquery = (
            ContentView.objects.filter(
                content_type=property_content_type, object_id=OuterRef("pkid")
            )
            .values("object_id")
            .annotate(count=Count("pkid"))
            .values("count")
        )
        queryset = (
            Property.objects.filter(owner=self.request.user)
            .select_related("property_type", "governorate", "city")
            .annotate(
                views_count=Coalesce(
                    Subquery(views_count_subquery, output_field=IntegerField()), 0
                ),
                visits_count=Count("visits"),
            )
            # ! Default Meta ordering is ignored on GROUP BY queries — set it
            # ! explicitly so pagination stays stable
            .order_by("-created_at")
        )
        rental_scope = self.request.query_params.get("rental_scope")
        if rental_scope:
            if rental_scope not in {"entire_property", "room", "room_group", "bed"}:
                return queryset.none()
            queryset = queryset.filter(rental_scopes__contains=f",{rental_scope},")
        return queryset


class PropertyUpdateAPIView(generics.UpdateAPIView):
    """
    API view to update details of an existing property listing.

    Request Body Example (PATCH):
    {
        "title": "Updated Apartment Title in Nasr City",
        "price": 13000.00,
        "is_furnished": false
    }
    """

    queryset = (
        Property.objects.select_related("owner", "property_type", "governorate", "city")
        .prefetch_related("images")
        .all()
    )
    serializer_class = PropertySerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = "id"

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), id=self.kwargs["id"])
        self.check_object_permissions(self.request, obj)
        return obj

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        data = PropertyDetailSerializer(
            updated_instance, context={"request": request}
        ).data
        return Response(
            {"message": "Property changes submitted for review.", **data},
            status=status.HTTP_200_OK,
        )


class PropertyDeleteAPIView(generics.DestroyAPIView):
    """
    API view to delete a property listing.
    """

    queryset = (
        Property.objects.select_related("owner", "property_type", "governorate", "city")
        .prefetch_related("images")
        .all()
    )
    serializer_class = PropertySerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    lookup_field = "id"

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), id=self.kwargs["id"])
        self.check_object_permissions(self.request, obj)
        return obj

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        property_id = PropertyService.delete_property(instance, request.user)
        return Response(
            {
                "message": "Property deleted successfully.",
                "id": property_id,
                "deleted": True,
            },
            status=status.HTTP_200_OK,
        )
