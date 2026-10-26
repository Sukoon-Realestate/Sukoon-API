"""Navigation reflects existing server permissions; it never grants authority."""

from rest_framework.exceptions import PermissionDenied
from core_apps.admin_api.permissions import (
    IsAdminStaff,
    IsFinancialStaff,
    IsPayoutStaff,
    IsRefundStaff,
    IsIdentityReviewer,
    IsPropertyReviewer,
    IsSupportStaff,
    IsSystemOwner,
    IsUserManager,
)
from core_apps.users.services.account_closure import require_reviewer


def allowed_paths(request):
    groups = (
        (
            IsAdminStaff,
            (
                "/",
                "/executive",
                "/analytics",
                "/reports/overview",
                "/users/reports",
                "/roles",
            ),
        ),
        (IsPropertyReviewer, ("/properties", "/properties/review", "/moderation")),
        (IsUserManager, ("/users", "/users/suspended", "/reports/chat-policy")),
        (IsIdentityReviewer, ("/kyc",)),
        (IsSupportStaff, ("/support",)),
        (IsFinancialStaff, ("/financials", "/financials/transactions")),
        (IsPayoutStaff, ("/financials/payouts",)),
        (IsRefundStaff, ("/financials/refunds",)),
        (
            IsSystemOwner,
            ("/notifications", "/settings", "/system/health", "/system/logs"),
        ),
    )
    paths = ["/security"]  # Own security and the independently authorized review.
    from core_apps.virtual_tours.review_access import reviewer
    from core_apps.virtual_tours.errors import TourError

    try:
        reviewer(request.user)
    except (PermissionDenied, TourError):
        pass
    else:
        paths.append("/properties/tours")
    for permission, destinations in groups:
        if permission().has_permission(request, None):
            paths.extend(destinations)
    try:
        require_reviewer(request)
    except PermissionDenied:
        pass
    else:
        paths.append("/account-closure")
    return paths
