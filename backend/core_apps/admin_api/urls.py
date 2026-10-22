from django.urls import path
from .views.session import AdminSessionAPIView
from .views.kyc import AdminKYCIdentityMediaAPIView
from .views import (
    AdminDashboardStatsView,
    AdminExecutiveDashboardStatsView,
    AdminPlatformSettingsAPIView,
    AdminUserListAPIView,
    AdminUserDetailAPIView,
    AdminUserSuspendAPIView,
    AdminUserUnsuspendAPIView,
    AdminKYCListAPIView,
    AdminKYCMetricsAPIView,
    AdminKYCDetailAPIView,
    AdminKYCApproveAPIView,
    AdminKYCRejectAPIView,
    AdminReportListAPIView,
    AdminReportActionAPIView,
    AdminReportMetricsAPIView,
    AdminSupportTicketsListAPIView,
    AdminSupportMetricsAPIView,
    AdminReportsOverviewAPIView,
    AdminStaffListAPIView,
    AdminRolesSummaryAPIView,
    AdminStaffInviteAPIView,
    AdminStaffDeleteAPIView,
    AdminPermissionsMatrixAPIView,
    AdminPropertyListAPIView,
    AdminPropertyMetricsAPIView,
    AdminPropertyDetailAPIView,
    AdminPropertyApproveAPIView,
    AdminPropertyRejectAPIView,
    AdminPropertyRevisionAPIView,
    AdminModerationListAPIView,
    AdminModerationMetricsAPIView,
    AdminModerationDeleteAPIView,
    AdminAnalyticsStatsAPIView,
    AdminFinancialSummaryAPIView,
    AdminTransactionListAPIView,
    AdminSystemHealthAPIView,
    AdminAuditLogsAPIView,
    AdminPushCampaignsAPIView,
    AdminSendPushNotificationAPIView,
)

from .views.system import AdminCampaignPreviewAPIView, AdminCampaignDetailAPIView

urlpatterns = [
    path("system/notifications/preview/", AdminCampaignPreviewAPIView.as_view(), name="admin-campaign-preview"),
    path("system/notifications/<uuid:campaign_id>/", AdminCampaignDetailAPIView.as_view(), name="admin-campaign-detail"),
    path("session/", AdminSessionAPIView.as_view(), name="admin-session"),
    # Dashboard stats
    path("dashboard/", AdminDashboardStatsView.as_view(), name="admin-dashboard-stats"),
    path("dashboard/executive/", AdminExecutiveDashboardStatsView.as_view(), name="admin-executive-dashboard"),
    path("settings/", AdminPlatformSettingsAPIView.as_view(), name="admin-settings"),
    
    # User management
    path("users/", AdminUserListAPIView.as_view(), name="admin-users-list"),
    path("users/<uuid:user_id>/", AdminUserDetailAPIView.as_view(), name="admin-user-detail"),
    path("users/<str:user_id>/", AdminUserDetailAPIView.as_view(), name="admin-user-detail-str"),
    path("users/<uuid:user_id>/suspend/", AdminUserSuspendAPIView.as_view(), name="admin-user-suspend"),
    path("users/<str:user_id>/suspend/", AdminUserSuspendAPIView.as_view(), name="admin-user-suspend-str"),
    path("users/<uuid:user_id>/unsuspend/", AdminUserUnsuspendAPIView.as_view(), name="admin-user-unsuspend"),
    path("users/<str:user_id>/unsuspend/", AdminUserUnsuspendAPIView.as_view(), name="admin-user-unsuspend-str"),

    # KYC verification queue
    path("kyc/<uuid:submission_id>/media/<slug:field>/", AdminKYCIdentityMediaAPIView.as_view(), name="admin-kyc-media"),
    path("kyc/", AdminKYCListAPIView.as_view(), name="admin-kyc-list"),
    path("kyc/metrics/", AdminKYCMetricsAPIView.as_view(), name="admin-kyc-metrics"),
    path("kyc/<uuid:submission_id>/", AdminKYCDetailAPIView.as_view(), name="admin-kyc-detail"),
    path("kyc/<str:submission_id>/", AdminKYCDetailAPIView.as_view(), name="admin-kyc-detail-str"),
    path("kyc/<uuid:submission_id>/approve/", AdminKYCApproveAPIView.as_view(), name="admin-kyc-approve"),
    path("kyc/<str:submission_id>/approve/", AdminKYCApproveAPIView.as_view(), name="admin-kyc-approve-str"),
    path("kyc/<uuid:submission_id>/reject/", AdminKYCRejectAPIView.as_view(), name="admin-kyc-reject"),
    path("kyc/<str:submission_id>/reject/", AdminKYCRejectAPIView.as_view(), name="admin-kyc-reject-str"),

    # Properties Management & Review
    path("properties/", AdminPropertyListAPIView.as_view(), name="admin-properties-list"),
    path("properties/metrics/", AdminPropertyMetricsAPIView.as_view(), name="admin-properties-metrics"),
    path("properties/<uuid:property_id>/", AdminPropertyDetailAPIView.as_view(), name="admin-property-detail"),
    path("properties/<str:property_id>/", AdminPropertyDetailAPIView.as_view(), name="admin-property-detail-str"),
    path("properties/<uuid:property_id>/approve/", AdminPropertyApproveAPIView.as_view(), name="admin-property-approve"),
    path("properties/<str:property_id>/approve/", AdminPropertyApproveAPIView.as_view(), name="admin-property-approve-str"),
    path("properties/<uuid:property_id>/reject/", AdminPropertyRejectAPIView.as_view(), name="admin-property-reject"),
    path("properties/<str:property_id>/reject/", AdminPropertyRejectAPIView.as_view(), name="admin-property-reject-str"),
    path("properties/<uuid:property_id>/revision/", AdminPropertyRevisionAPIView.as_view(), name="admin-property-revision"),
    path("properties/<str:property_id>/revision/", AdminPropertyRevisionAPIView.as_view(), name="admin-property-revision-str"),

    # Content Moderation
    path("moderation/", AdminModerationListAPIView.as_view(), name="admin-moderation-list"),
    path("moderation/metrics/", AdminModerationMetricsAPIView.as_view(), name="admin-moderation-metrics"),
    path("moderation/<uuid:property_id>/delete/", AdminModerationDeleteAPIView.as_view(), name="admin-moderation-delete"),
    path("moderation/<str:property_id>/delete/", AdminModerationDeleteAPIView.as_view(), name="admin-moderation-delete-str"),

    # User Reports & Violations
    path("reports/", AdminReportListAPIView.as_view(), name="admin-reports-list"),
    path("reports/metrics/", AdminReportMetricsAPIView.as_view(), name="admin-reports-metrics"),
    path("reports/overview/", AdminReportsOverviewAPIView.as_view(), name="admin-reports-overview"),
    path("reports/<uuid:report_id>/action/", AdminReportActionAPIView.as_view(), name="admin-report-action"),
    path("reports/<str:report_id>/action/", AdminReportActionAPIView.as_view(), name="admin-report-action-str"),

    # Support Tickets & Customer Support
    path("support/", AdminSupportTicketsListAPIView.as_view(), name="admin-support-list"),
    path("support/metrics/", AdminSupportMetricsAPIView.as_view(), name="admin-support-metrics"),

    # Analytics & Reports
    path("analytics/", AdminAnalyticsStatsAPIView.as_view(), name="admin-analytics-stats"),

    # Financials & System
    path("financials/summary/", AdminFinancialSummaryAPIView.as_view(), name="admin-financials-summary"),
    path("financials/transactions/", AdminTransactionListAPIView.as_view(), name="admin-financials-transactions"),
    path("system/health/", AdminSystemHealthAPIView.as_view(), name="admin-system-health"),
    path("system/logs/", AdminAuditLogsAPIView.as_view(), name="admin-system-logs"),
    path("system/notifications/", AdminPushCampaignsAPIView.as_view(), name="admin-system-notifications"),
    path("system/notifications/send/", AdminSendPushNotificationAPIView.as_view(), name="admin-system-notifications-send"),

    # Staff Roles & Permissions
    path("staff/", AdminStaffListAPIView.as_view(), name="admin-staff-list"),
    path("staff/roles/", AdminRolesSummaryAPIView.as_view(), name="admin-roles-summary"),
    path("staff/invite/", AdminStaffInviteAPIView.as_view(), name="admin-staff-invite"),
    path("staff/<uuid:staff_id>/", AdminStaffDeleteAPIView.as_view(), name="admin-staff-delete"),
    path("staff/<str:staff_id>/", AdminStaffDeleteAPIView.as_view(), name="admin-staff-delete-str"),
    path("permissions/", AdminPermissionsMatrixAPIView.as_view(), name="admin-permissions-matrix"),
]

from core_apps.features import reputation_views as rating_views
urlpatterns += [
    path("reviews/", rating_views.ReviewModerationQueueView.as_view()),
    path("review-cases/", rating_views.ReviewOperatorCasesView.as_view()),
    path("review-cases/<uuid:identity>/resolve/", rating_views.ReviewResolveCaseView.as_view()),
    path("reviews/<uuid:identity>/decisions/", rating_views.ReviewModerateView.as_view()),
    path("review-appeals/<uuid:identity>/resolve/", rating_views.ReviewResolveAppealView.as_view()),
]

from core_apps.features import reputation_experience_views as review_experiences
urlpatterns += [
    path("review-recovery/", review_experiences.ReviewRecoveryView.as_view()),
    path("review-windows/<uuid:identity>/extend/", review_experiences.ReviewWindowExtensionView.as_view()),
]
