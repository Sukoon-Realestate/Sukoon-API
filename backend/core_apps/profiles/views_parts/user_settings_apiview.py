"""Views: user settings apiview."""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from core_apps.common.pagination import (
    ClientResultsSetPagination,
    StandardResultsSetPagination,
)
from core_apps.common.renderers import GenericJsonRenderer
from ..models import Contract, UserSettings
from ..serializers import (
    OwnerUnreadCountsSerializer,
    TenantContractSerializer,
    TenantMyRateSerializer,
    TenantUnreadCountsSerializer,
    UserSettingsSerializer,
    VerificationStatusSerializer,
)
from ..services import ProfileService
from core_apps.properties.models import PropertyVisitReview


class UserSettingsAPIView(generics.RetrieveUpdateAPIView):
    """
    Screen: 'الإعدادات والخصوصية' (Settings & Privacy).

    GET: Returns user notification and privacy settings with grouped UI sections.

    PUT/PATCH: Updates user notification and privacy settings.

    Request Body Example (PATCH / PUT):
    {
        "visit_notifications": true,
        "new_properties_in_area": true,
        "owner_messages": true,
        "promotions_and_updates": false,
        "share_location_for_search": true,
        "show_profile_in_search": false
    }

    Nested payload is also supported:
    {
        "notifications": {
            "visit_notifications": false
        },
        "privacy": {
            "show_profile_in_search": true
        }
    }
    """

    serializer_class = UserSettingsSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> UserSettings:
        return ProfileService.get_user_settings(self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        settings_obj = ProfileService.update_user_settings(
            user=request.user, validated_data=serializer.validated_data
        )

        response_serializer = self.get_serializer(settings_obj)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class OwnerUnreadCountsAPIView(generics.GenericAPIView):
    """
    Returns badge / unread counts for an owner account:
    - visit_requests_count (pending requests awaiting decision)
    - unread_chat_messages_count (account-wide unread messages)
    - unread_notifications_count (account-wide unread notifications)
    """

    serializer_class = OwnerUnreadCountsSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs) -> Response:
        data = ProfileService.get_owner_unread_counts(request.user)
        serializer = self.get_serializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TenantUnreadCountsAPIView(generics.GenericAPIView):
    """
    Returns badge / unread counts for a tenant account:
    - favorites_count (saved properties)
    - unread_chat_messages_count (account-wide unread messages)
    - unread_notifications_count (account-wide unread notifications)
    - visit_requests_count (active visit requests)
    """

    serializer_class = TenantUnreadCountsSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs) -> Response:
        data = ProfileService.get_tenant_unread_counts(request.user)
        serializer = self.get_serializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TenantMyRatesListAPIView(generics.ListAPIView):
    """
    Returns paginated list of reviews and ratings submitted by the authenticated tenant.
    """

    serializer_class = TenantMyRateSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return (
            PropertyVisitReview.objects.filter(visit__tenant=self.request.user)
            .select_related("visit", "visit__property")
            .order_by("-created_at")
        )


class VerificationStatusAPIView(generics.RetrieveAPIView):
    """
    GET profiles/verification-status/
    Returns shared identity verification status for the authenticated user.
    Statuses: incomplete, pending, approved, rejected.
    """

    serializer_class = VerificationStatusSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs) -> Response:
        data = ProfileService.get_verification_status(request.user)
        serializer = self.get_serializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TenantContractsListAPIView(generics.ListAPIView):
    """
    GET profiles/contracts/?page=1&page_size=20
    Returns paginated contracts for the authenticated tenant.
    """

    serializer_class = TenantContractSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ClientResultsSetPagination

    def get_queryset(self):
        return (
            Contract.objects.filter(tenant=self.request.user)
            .select_related("property")
            .order_by("-created_at")
        )
