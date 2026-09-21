from .dashboard import AdminDashboardStatsView
from .users import (
    AdminUserListAPIView,
    AdminUserDetailAPIView,
    AdminUserSuspendAPIView,
    AdminUserUnsuspendAPIView,
)
from .kyc import (
    AdminKYCListAPIView,
    AdminKYCMetricsAPIView,
    AdminKYCDetailAPIView,
    AdminKYCApproveAPIView,
    AdminKYCRejectAPIView,
)
from .reports import (
    AdminReportListAPIView,
    AdminReportActionAPIView,
)
from .staff import (
    AdminStaffListAPIView,
    AdminRolesSummaryAPIView,
    AdminStaffInviteAPIView,
    AdminStaffDeleteAPIView,
    AdminPermissionsMatrixAPIView,
)
from .property_views import (
    AdminPropertyListAPIView,
    AdminPropertyMetricsAPIView,
    AdminPropertyDetailAPIView,
    AdminPropertyApproveAPIView,
    AdminPropertyRejectAPIView,
    AdminPropertyRevisionAPIView,
)

__all__ = [
    "AdminDashboardStatsView",
    "AdminUserListAPIView",
    "AdminUserDetailAPIView",
    "AdminUserSuspendAPIView",
    "AdminUserUnsuspendAPIView",
    "AdminKYCListAPIView",
    "AdminKYCMetricsAPIView",
    "AdminKYCDetailAPIView",
    "AdminKYCApproveAPIView",
    "AdminKYCRejectAPIView",
    "AdminReportListAPIView",
    "AdminReportActionAPIView",
    "AdminStaffListAPIView",
    "AdminRolesSummaryAPIView",
    "AdminStaffInviteAPIView",
    "AdminStaffDeleteAPIView",
    "AdminPermissionsMatrixAPIView",
    "AdminPropertyListAPIView",
    "AdminPropertyMetricsAPIView",
    "AdminPropertyDetailAPIView",
    "AdminPropertyApproveAPIView",
    "AdminPropertyRejectAPIView",
    "AdminPropertyRevisionAPIView",
]
