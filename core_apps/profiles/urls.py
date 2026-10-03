from django.urls import path
from core_apps.users.views import UserDeleteAPIView

from .views import (
    AccountSummaryDetailAPIView,
    MyAccountDetailAPIView,
    OwnerUnreadCountsAPIView,
    ProfileDetailAPIView,
    ProfileEditAPIView,
    ProfileListAPIView,
    ProfileUpdateAPIView,
    TenantMyRatesListAPIView,
    TenantUnreadCountsAPIView,
    UserSettingsAPIView,
    VerificationStatusAPIView,
    TenantContractsListAPIView,
)

urlpatterns = [
    path("all/", ProfileListAPIView.as_view(), name="profile-list"),
    path("user/my-profile/", ProfileDetailAPIView.as_view(), name="profile-detail"),
    path("user/update/", ProfileUpdateAPIView.as_view(), name="profile-update"),
    # * Mobile Screen Endpoints
    path("my-account/", MyAccountDetailAPIView.as_view(), name="my-account"),
    path(
        "account-summary/",
        AccountSummaryDetailAPIView.as_view(),
        name="account-summary",
    ),
    path("edit/", ProfileEditAPIView.as_view(), name="profile-edit"),
    path("settings/", UserSettingsAPIView.as_view(), name="user-settings"),
    path(
        "verification-status/",
        VerificationStatusAPIView.as_view(),
        name="verification-status",
    ),
    path(
        "contracts/", TenantContractsListAPIView.as_view(), name="tenant-contracts-list"
    ),
    path("delete-account/", UserDeleteAPIView.as_view(), name="profile-delete-account"),
    path(
        "owner/unread-counts/",
        OwnerUnreadCountsAPIView.as_view(),
        name="owner-unread-counts",
    ),
    path(
        "tenant/unread-counts/",
        TenantUnreadCountsAPIView.as_view(),
        name="tenant-unread-counts",
    ),
    path("my-rates/", TenantMyRatesListAPIView.as_view(), name="tenant-my-rates"),
]
