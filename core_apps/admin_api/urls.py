from django.urls import path
from .views import (
    AdminDashboardStatsView,
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
)

urlpatterns = [
    # Dashboard stats
    path("dashboard/", AdminDashboardStatsView.as_view(), name="admin-dashboard-stats"),
    
    # User management
    path("users/", AdminUserListAPIView.as_view(), name="admin-users-list"),
    path("users/<uuid:user_id>/", AdminUserDetailAPIView.as_view(), name="admin-user-detail"),
    path("users/<str:user_id>/", AdminUserDetailAPIView.as_view(), name="admin-user-detail-str"),
    path("users/<uuid:user_id>/suspend/", AdminUserSuspendAPIView.as_view(), name="admin-user-suspend"),
    path("users/<str:user_id>/suspend/", AdminUserSuspendAPIView.as_view(), name="admin-user-suspend-str"),
    path("users/<uuid:user_id>/unsuspend/", AdminUserUnsuspendAPIView.as_view(), name="admin-user-unsuspend"),
    path("users/<str:user_id>/unsuspend/", AdminUserUnsuspendAPIView.as_view(), name="admin-user-unsuspend-str"),

    # KYC verification queue
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

    # User Reports & Violations
    path("reports/", AdminReportListAPIView.as_view(), name="admin-reports-list"),
    path("reports/<uuid:report_id>/action/", AdminReportActionAPIView.as_view(), name="admin-report-action"),
    path("reports/<str:report_id>/action/", AdminReportActionAPIView.as_view(), name="admin-report-action-str"),

    # Staff Roles & Permissions
    path("staff/", AdminStaffListAPIView.as_view(), name="admin-staff-list"),
    path("staff/roles/", AdminRolesSummaryAPIView.as_view(), name="admin-roles-summary"),
    path("staff/invite/", AdminStaffInviteAPIView.as_view(), name="admin-staff-invite"),
    path("staff/<uuid:staff_id>/", AdminStaffDeleteAPIView.as_view(), name="admin-staff-delete"),
    path("staff/<str:staff_id>/", AdminStaffDeleteAPIView.as_view(), name="admin-staff-delete-str"),
    path("permissions/", AdminPermissionsMatrixAPIView.as_view(), name="admin-permissions-matrix"),
]
