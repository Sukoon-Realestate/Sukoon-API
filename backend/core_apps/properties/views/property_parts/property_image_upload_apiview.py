"""Property: property image upload apiview."""

from django.shortcuts import get_object_or_404
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

        def upload_image():
            img_obj = PropertyService.upload_property_image(
                property_obj=property_obj,
                image=serializer.validated_data["image"],
                name=serializer.validated_data.get("name", ""),
                description=serializer.validated_data.get("description", ""),
            )
            data = PropertyImageSerializer(img_obj, context={"request": request}).data
            return (
                {"message": "Image uploaded successfully.", **data},
                status.HTTP_201_CREATED,
                img_obj.id,
            )

        data, response_status, replayed = execute_idempotent(
            user=request.user,
            operation=f"property.image.upload:{property_obj.id}",
            key=request_key,
            payload=serializer.validated_data,
            action=upload_image,
            request_subject_id=property_obj.id,
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
