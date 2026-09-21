import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from core_apps.admin_api.permissions import IsAdminStaff
from core_apps.admin_api.serializers import (
    AdminUserListSerializer,
    AdminUserSuspendSerializer,
)
from core_apps.admin_api.services import (
    get_admin_users_queryset,
    get_admin_user_detail,
    suspend_user,
    unsuspend_user,
)
from core_apps.admin_api.filters import AdminUserFilter

logger = logging.getLogger(__name__)


class AdminUserListAPIView(generics.ListAPIView):
    """
    Returns a paginated list of all platform users with filtering and search capabilities.
    """

    permission_classes = [IsAdminStaff]
    serializer_class = AdminUserListSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AdminUserFilter
    ordering_fields = ["date_joined", "first_name", "email"]
    ordering = ["-date_joined"]

    def get_queryset(self):
        return get_admin_users_queryset()


class AdminUserDetailAPIView(APIView):
    """
    Returns full details for a single user, including profile information,
    property listings, KYC status, and recent activity logs.
    """

    permission_classes = [IsAdminStaff]

    def get(self, request, user_id):
        user_detail = get_admin_user_detail(user_id)
        return Response(user_detail, status=status.HTTP_200_OK)


class AdminUserSuspendAPIView(APIView):
    """
    Suspends a user account.

    Request Body:
    {
        "reason": "مخالفة شروط الاستخدام ونشر إعلانات وهمية"
    }
    """

    permission_classes = [IsAdminStaff]

    def post(self, request, user_id):
        serializer = AdminUserSuspendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("reason", "إيقاف إداري للحساب")

        user = suspend_user(user_id=user_id, admin_user=request.user, reason=reason)
        return Response(
            {"message": f"تم إيقاف حساب المستخدم {user.get_full_name or user.email} بنجاح."},
            status=status.HTTP_200_OK,
        )


class AdminUserUnsuspendAPIView(APIView):
    """
    Reactivates a previously suspended user account.
    """

    permission_classes = [IsAdminStaff]

    def post(self, request, user_id):
        user = unsuspend_user(user_id=user_id, admin_user=request.user)
        return Response(
            {"message": f"تم إعادة تنشيط حساب المستخدم {user.get_full_name or user.email} بنجاح."},
            status=status.HTTP_200_OK,
        )
