"""Property: property detail apiview."""

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Avg, BooleanField, Exists, FloatField, OuterRef, Q, Value
from django.db.models.functions import Coalesce
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from core_apps.common.models import ContentView
from core_apps.common.idempotency import (
    execute_idempotent,
    request_key as get_idempotency_key,
    response_headers,
)
from core_apps.common.renderers import GenericJsonRenderer
from ...models import Property, PropertyFavorite, SavedProperty
from ...serializers import PropertyDetailSerializer, PropertySerializer
from .property_filter_options_apiview import get_client_ip


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
        "governorate": "<governorate-uuid>",
        "city": "<city-uuid>",
        "district": "Nasr City",
        "latitude": 30.0444,
        "longitude": 31.2357,
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

    def create(self, request, *args, **kwargs):
        rental_version = request.headers.get("X-Rental-Offers-Version")
        request_key = get_idempotency_key(request)
        if rental_version and rental_version != "1":
            return Response(
                {"message": "Unsupported rental offers version."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if rental_version == "1" and not request_key:
            return Response(
                {
                    "message": "Idempotency-Key is required for rental inventory creation."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request_key and not request.user.is_verified:
            raise permissions.exceptions.PermissionDenied(
                "Identity verification is required for recoverable listing writes."
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data)
        if "rental_inventory" in payload:
            # Validation assigns fresh server IDs. They describe the result,
            # not the original command, and must not change its retry identity.
            import json

            inventory = request.data["rental_inventory"]
            payload["rental_inventory"] = (
                json.loads(inventory) if isinstance(inventory, str) else inventory
            )

        def create_property():
            self.perform_create(serializer)
            data = serializer.data
            return data, status.HTTP_201_CREATED, serializer.instance.id

        data, response_status, replayed = execute_idempotent(
            user=request.user,
            auth_claims=request.auth,
            operation="property.create",
            key=request_key,
            payload=payload,
            action=create_property,
        )
        return Response(
            data,
            status=response_status,
            headers=response_headers(replayed),
        )


class PropertyDetailAPIView(generics.RetrieveUpdateAPIView):
    """
    API view to retrieve or update details of a single property listing.
    """

    serializer_class = PropertyDetailSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.AllowAny]
    lookup_field = "id"
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        queryset = Property.objects.select_related(
            "owner",
            "owner__profile",
            "property_type",
            "governorate",
            "city",
            "city__governorate",
        ).prefetch_related("images")
        request_user = self.request.user
        # Split/merge predecessors remain historical identities, never public
        # offers. Contract participants retain their canonical lease documents.
        if not getattr(request_user, "is_staff", False):
            from ...services.public_access import public_properties
            visible = Q(pk__in=public_properties().values('pk'))
            if request_user.is_authenticated:
                visible |= Q(owner=request_user)
            queryset = queryset.filter(visible)
        if request_user.is_authenticated:
            queryset = queryset.annotate(
                is_fav=Exists(
                    PropertyFavorite.objects.filter(
                        user=request_user, property=OuterRef("pkid")
                    )
                ),
                is_saved=Exists(
                    SavedProperty.objects.filter(
                        user=request_user, property=OuterRef("pkid")
                    )
                ),
            )
        else:
            queryset = queryset.annotate(
                is_fav=Value(False, output_field=BooleanField()),
                is_saved=Value(False, output_field=BooleanField()),
            )
        return queryset.annotate(
            rating=Coalesce(
                Avg("ratings__rating"),
                Value(0.0),
                output_field=FloatField(),
            )
        )

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

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_authenticated or (
            instance.owner != request.user
            and not getattr(request.user, "is_staff", False)
        ):
            raise permissions.exceptions.PermissionDenied(
                "You are not the owner of this property listing."
            )
        key = get_idempotency_key(request)

        def update_property():
            with transaction.atomic():
                current = Property.objects.select_for_update().get(pk=instance.pk)
                if current.owner_id != request.user.pk:
                    raise permissions.exceptions.PermissionDenied(
                        "Only the current owner can edit a listing."
                    )
                expected = request.headers.get("If-Unmodified-Since")
                from django.utils.dateparse import parse_datetime

                try:
                    matches = (
                        not expected or parse_datetime(expected) == current.updated_at
                    )
                except (ValueError, TypeError):
                    matches = False
                if not matches:
                    from core_apps.common.idempotency import IdempotencyConflict

                    raise IdempotencyConflict(
                        "Property changed. Reload and review before saving."
                    )
                serializer = PropertySerializer(
                    current,
                    data=request.data,
                    partial=True,
                    context={"request": request},
                )
                serializer.is_valid(raise_exception=True)
                updated = serializer.save()
                data = PropertyDetailSerializer(
                    updated, context={"request": request}
                ).data
                return (
                    {"message": "Property changes submitted for review.", **data},
                    200,
                    updated.id,
                )

        payload = (
            {
                key: (
                    request.data.getlist(key)
                    if len(request.data.getlist(key)) > 1
                    else request.data.get(key)
                )
                for key in request.data
            }
            if hasattr(request.data, "getlist")
            else dict(request.data)
        )
        payload["expected_updated_at"] = request.headers.get("If-Unmodified-Since", "")
        data, response_status, replayed = execute_idempotent(
            user=request.user,
            auth_claims=request.auth,
            operation=f"property.update:{instance.id}",
            key=key,
            payload=payload,
            action=update_property,
            request_subject_id=instance.id,
        )
        return Response(
            data, status=response_status, headers=response_headers(replayed)
        )
