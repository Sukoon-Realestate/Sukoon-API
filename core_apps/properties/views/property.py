import logging

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.db.models import Count, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from core_apps.common.models import ContentView
from core_apps.common.renderers import GenericJsonRenderer

from ..filters import PropertyFilter
from ..models import Property, PropertyImage, PropertyType
from ..permissions import IsOwnerOrReadOnly
from ..serializers import (
    MyPropertyListSerializer,
    PropertyImageSerializer,
    PropertyImageUpdateSerializer,
    PropertyImageUploadSerializer,
    PropertyListSerializer,
    PropertySerializer,
    PropertyTypeSerializer,
)
from ..services import PropertyService

logger = logging.getLogger(__name__)


def get_client_ip(request):
    # ? Behind a proxy the real client IP is the first entry of X-Forwarded-For
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class PropertyPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = "page_size"
    max_page_size = 100


class PropertyTypeListAPIView(generics.ListAPIView):
    """
    API view to list available property types (managed by admins).

    Returns all PropertyType records: id, name, slug, description.
    """

    queryset = PropertyType.objects.all()
    serializer_class = PropertyTypeSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]


class PropertyListAPIView(generics.ListAPIView):
    """
    API view to list properties.
    """

    queryset = Property.objects.select_related("property_type").annotate(images_count=Count("images")).order_by("-created_at")
    serializer_class = PropertyListSerializer
    renderer_classes = [GenericJsonRenderer]
    pagination_class = PropertyPagination
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PropertyFilter
    search_fields = ["title", "description", "city", "district"]
    ordering_fields = ["price", "created_at"]


class PropertyCreateAPIView(generics.CreateAPIView):
    """
    API view to create a property listing.

    Request Body Example:
    {
        "title": "Beautiful Apartment in Nasr City",
        "description": "A spacious 3-room fully furnished apartment.",
        "price": 12000.00,
        "price_period": "monthly",
        "property_type": "apartment",
        "is_furnished": true,
        "bedrooms": 3,
        "bathrooms": 2,
        "area": 120,
        "floor": 4,
        "rental_period": 6,
        "suitable_for": "families",
        "smoking_allowed": false,
        "city": "Cairo",
        "district": "Nasr City",
        "has_wifi": true,
        "has_elevator": true,
        "has_garage": false,
        "has_security": true,
        "has_balcony": true,
        "has_air_conditioning": true,
        "near_metro": true,
        "has_natural_gas": true
    }
    """

    queryset = Property.objects.none()
    serializer_class = PropertySerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PropertyDetailAPIView(generics.RetrieveAPIView):
    """
    API view to retrieve details of a single property listing.
    """

    queryset = Property.objects.select_related("owner", "property_type").prefetch_related("images").all()
    serializer_class = PropertySerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.AllowAny]
    lookup_field = "id"

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), id=self.kwargs["id"])
        self.check_object_permissions(self.request, obj)
        return obj

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # * Track the view so owners see real "number of views" stats
        ContentView.record_view(
            content_object=instance,
            user=request.user if request.user.is_authenticated else None,
            viewer_ip=get_client_ip(request),
        )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


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
        return (
            Property.objects.filter(owner=self.request.user).select_related("property_type").annotate(
                views_count=Coalesce(
                    Subquery(views_count_subquery, output_field=IntegerField()), 0
                ),
                visits_count=Count("visits"),
            )
            # ! Default Meta ordering is ignored on GROUP BY queries — set it
            # ! explicitly so pagination stays stable
            .order_by("-created_at")
        )


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

    queryset = Property.objects.select_related("owner", "property_type").prefetch_related("images").all()
    serializer_class = PropertySerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = "id"

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), id=self.kwargs["id"])
        self.check_object_permissions(self.request, obj)
        return obj


class PropertyDeleteAPIView(generics.DestroyAPIView):
    """
    API view to delete a property listing.
    """

    queryset = Property.objects.select_related("owner", "property_type").prefetch_related("images").all()
    serializer_class = PropertySerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = "id"

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), id=self.kwargs["id"])
        self.check_object_permissions(self.request, obj)
        return obj


class PropertyImageUploadAPIView(generics.CreateAPIView):
    """
    API view to upload an image with its metadata for a property listing.
    """

    queryset = PropertyImage.objects.all()
    serializer_class = PropertyImageUploadSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        property_obj = get_object_or_404(
            Property.objects.all(), id=self.kwargs["property_id"]
        )
        if property_obj.owner != self.request.user:
            raise permissions.exceptions.PermissionDenied(
                "You are not the owner of this property listing."
            )
        serializer.save(property=property_obj)


class PropertyImageDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, update, or delete a specific property image.

    Request Body Example (PATCH):
    {
        "name": "Master Bedroom",
        "description": "Spacious bedroom with natural lighting"
    }
    """

    queryset = PropertyImage.objects.select_related("property").all()
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return PropertyImageUpdateSerializer
        return PropertyImageSerializer

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), id=self.kwargs["id"])
        if (
            self.request.method not in permissions.SAFE_METHODS
            and obj.property.owner != self.request.user
        ):
            raise permissions.exceptions.PermissionDenied(
                "You are not the owner of the related property listing."
            )
        return obj
