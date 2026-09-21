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
    AdminReportMetricsAPIView,
    AdminSupportTicketsListAPIView,
    AdminSupportMetricsAPIView,
    AdminReportsOverviewAPIView,
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
from .moderation import (
    AdminModerationListAPIView,
    AdminModerationMetricsAPIView,
    AdminModerationDeleteAPIView,
)
from .analytics import AdminAnalyticsStatsAPIView
from .financials import (
    AdminFinancialSummaryAPIView,
    AdminTransactionListAPIView,
)
from .system import (
    AdminSystemHealthAPIView,
    AdminAuditLogsAPIView,
    AdminPushCampaignsAPIView,
    AdminSendPushNotificationAPIView,
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
    "AdminReportMetricsAPIView",
    "AdminSupportTicketsListAPIView",
    "AdminSupportMetricsAPIView",
    "AdminReportsOverviewAPIView",
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
    "AdminModerationListAPIView",
    "AdminModerationMetricsAPIView",
    "AdminModerationDeleteAPIView",
    "AdminAnalyticsStatsAPIView",
    "AdminFinancialSummaryAPIView",
    "AdminTransactionListAPIView",
    "AdminSystemHealthAPIView",
    "AdminAuditLogsAPIView",
    "AdminPushCampaignsAPIView",
    "AdminSendPushNotificationAPIView",
]
