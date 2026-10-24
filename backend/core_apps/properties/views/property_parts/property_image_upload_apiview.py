"""Property: property image upload apiview."""

from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from core_apps.common.idempotency import (
    execute_idempotent,
    request_key as get_idempotency_key,
    response_headers,
)
from core_apps.common.renderers import GenericJsonRenderer
from ...models import Property, PropertyImage
from ...permissions import IsOwner
from ...serializers import (
    PropertyImageSerializer,
    PropertyImageUpdateSerializer,
    PropertyImageUploadSerializer,
    PropertyStatisticsSerializer,
    PropertyVisibilitySerializer,
)
from ...services import PropertyService


class PropertyImageUploadAPIView(generics.CreateAPIView):
    """
    API view to upload an image with its metadata for a property listing.
    """

    queryset = PropertyImage.objects.all()
    serializer_class = PropertyImageUploadSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        property_obj = get_object_or_404(
            Property.objects.all(), id=self.kwargs["property_id"]
        )
        if property_obj.owner != request.user and not getattr(
            request.user, "is_staff", False
        ):
            raise permissions.exceptions.PermissionDenied(
                "You are not the owner of this property listing."
            )
        request_key = get_idempotency_key(request)
        if request_key and not request.user.is_verified:
            raise permissions.exceptions.PermissionDenied(
                "Identity verification is required for recoverable image uploads."
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from ...services.image_uploads import upload
        import uuid
        data, response_status, replayed = upload(
            user=request.user, claims=request.auth, property_obj=property_obj,
            key=request_key or str(uuid.uuid4()), data=serializer.validated_data,
            require_verified=bool(request_key),
        )
        return Response(
            data,
            status=response_status,
            headers=response_headers(replayed),
        )


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

    def get_queryset(self):
        from ...services.public_access import public_properties
        from django.db.models import Q
        if self.request.user.is_staff:
            return super().get_queryset()
        allowed = Q(property__in=public_properties())
        if self.request.user.is_authenticated:
            allowed |= Q(property__owner=self.request.user)
        return super().get_queryset().filter(allowed)

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


    def _lock_write(self):
        from core_apps.users.models import User
        from ...services.image_uploads import _authority

        current = User.objects.select_for_update().get(pk=self.request.user.pk)
        image = get_object_or_404(PropertyImage, id=self.kwargs["id"])
        prop = Property.objects.select_for_update().get(pk=image.property_id)
        _authority(current, prop, self.request.auth)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        self._lock_write()
        return super().update(request, *args, **kwargs)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        self._lock_write()
        return super().destroy(request, *args, **kwargs)


class PropertyStatisticsAPIView(generics.RetrieveAPIView):
    """
    API view to retrieve detailed performance and engagement statistics for
    an owner's property listing.
    """

    queryset = Property.objects.select_related("owner").all()
    serializer_class = PropertyStatisticsSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    lookup_field = "id"

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), id=self.kwargs["id"])
        self.check_object_permissions(self.request, obj)
        return obj

    def retrieve(self, request, *args, **kwargs):
        property_obj = self.get_object()
        period = request.query_params.get("period", "30_days")
        data = PropertyService.get_property_statistics(property_obj, period=period)
        serializer = self.get_serializer(data)
        return Response(serializer.data)


class PropertyToggleVisibilityAPIView(generics.GenericAPIView):
    """
    API view for an owner to toggle or update the visibility (hide/unhide) of
    their property listing.

    POST toggles between hidden and active/verified.
    PATCH accepts {"is_hidden": true|false}.
    """

    queryset = Property.objects.select_related("owner").all()
    serializer_class = PropertyVisibilitySerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    lookup_field = "id"

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), id=self.kwargs["id"])
        self.check_object_permissions(self.request, obj)
        return obj

    def post(self, request, *args, **kwargs):
        property_obj = self.get_object()
        is_hidden = (
            request.data.get("is_hidden")
            if isinstance(request.data, dict) and "is_hidden" in request.data
            else None
        )
        updated_obj = PropertyService.toggle_property_visibility(
            property_obj, is_hidden=is_hidden
        )
        is_now_hidden = updated_obj.status == Property.Status.HIDDEN
        message = (
            "Property is now hidden." if is_now_hidden else "Property is now visible."
        )
        serializer = self.get_serializer(
            {
                "id": updated_obj.id,
                "title": updated_obj.title,
                "status": updated_obj.status,
                "is_hidden": is_now_hidden,
                "message": message,
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)
