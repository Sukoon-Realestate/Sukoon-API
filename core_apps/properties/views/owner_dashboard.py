import logging

from rest_framework import generics, permissions
from rest_framework.response import Response

from core_apps.common.renderers import GenericJsonRenderer

from ..serializers import (
    OwnerDashboardSerializer,
    OwnerProfileSerializer,
    OwnerRevenuesSerializer,
)
from ..services import OwnerDashboardService

logger = logging.getLogger(__name__)


class OwnerDashboardAPIView(generics.GenericAPIView):
    """
    API view to return the authenticated property owner's dashboard summary.

    Response includes the owner's profile header, key stats (weekly visits,
    active properties, overall rating, pending requests) and a list of pending
    visit requests awaiting the owner's response.
    """

    serializer_class = OwnerDashboardSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        dashboard_data = OwnerDashboardService.get_dashboard(owner=request.user)
        serializer = self.get_serializer(dashboard_data)
        return Response(serializer.data)


class OwnerRevenuesAPIView(generics.GenericAPIView):
    """
    API view to return the authenticated property owner's revenue and earnings summary
    matching the mobile "الإيرادات" screen.

    Response includes:
    - total_this_month and comparison text (+8% عن الشهر السابق)
    - per-property breakdown cards with statuses (مدفوع, قادم 15 يونيو, متأخر)
    - recent transactions list
    """

    serializer_class = OwnerRevenuesSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        revenue_data = OwnerDashboardService.get_revenues(owner=request.user)
        serializer = self.get_serializer(revenue_data)
        return Response(serializer.data)


class OwnerProfileAPIView(generics.GenericAPIView):
    """
    API view for the authenticated property owner's profile screen ("ملفي الشخصي").

    Response includes:
    - owner header: avatar, is_verified, full_name, role_badge ("مالك موثّق"),
      average rating, reviews count, rating label ("4.8 (42 تقييم)"), member since label.
    - stats: properties_count ("3 عقارات"), reviews_count ("42 تقييم"), acceptance_rate ("96% قبول").
    - account_details: name, email, mobile phone with masking ("010****432").
    - privacy_notice: "رقمك لا يُعرض للمستأجرين – يظهر فقط بعد قبول الزيارة".
    - recent_reviews: list of recent visit reviews.
    """

    serializer_class = OwnerProfileSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        profile_data = OwnerDashboardService.get_owner_profile(owner=request.user)
        serializer = self.get_serializer(profile_data)
        return Response(serializer.data)
