"""Reversible MVP release boundary; deferred implementations stay in source."""

import re

from django.conf import settings
from django.http import JsonResponse


FEATURE_ROOTS = frozenset({
    "business-policies", "configuration", "planning-capabilities",
    "search-alerts", "commute-searches", "tenant-assistant",
    "decision-notebook", "experience", "listing-suggestions", "owner-analytics",
    "residential-assets", "residential-changes", "residential-media",
    "residential-unit-templates", "residential-unit-batches",
})
PROPERTY_DEFERRED_NAMES = frozenset({
    "post-visit-decision", "viewing-representatives", "owner-revenues",
    "owner-earnings", "property-visit-review-create",
})
PROFILE_DEFERRED_NAMES = frozenset({
    "tenant-contracts-list", "tenant-my-rates", "account-summary",
})


def enabled():
    return getattr(settings, "SUKOON_MVP", True)


def allows_path(path, url_name=None, method="GET"):
    """Keep auth, discovery, inventory, viewings, direct chat and account tools.

    Provider callbacks intentionally remain reachable to reconcile existing
    transactions; this switch must never discard an in-flight payment event.
    """
    if not enabled():
        return True
    if path.startswith('/api/v1/admin/'):
        root = path.removeprefix('/api/v1/admin/').split('/', 1)[0]
        if root in {'financials', 'reviews', 'review-cases', 'review-appeals',
                    'review-recovery', 'review-windows'}:
            return False
    if path == "/api/v1/features/v1/signing/provider-events/":
        return True
    if path == "/api/v1/features/v1/workspace-summary/":
        return method in {"GET", "HEAD", "OPTIONS"}
    if path == '/api/v1/features/v1/operator/business-policies/':
        return method in {'GET', 'HEAD', 'POST', 'OPTIONS'}
    if path.startswith('/api/v1/features/v1/experience/preparation-tasks/'):
        return False
    if path.startswith("/api/v1/features/v1/reviews/"):
        tail = path.removeprefix("/api/v1/features/v1/reviews/")
        return method in {"GET", "HEAD", "OPTIONS"} and (
            tail == "capabilities/" or tail.startswith(("subjects/", "portfolios/", "properties/"))
            or bool(re.fullmatch(r"[0-9a-fA-F-]{36}/", tail))
        )
    if path.startswith("/api/v1/features/v1/"):
        tail = path.removeprefix("/api/v1/features/v1/")
        root = tail.split("/", 1)[0]
        return root in FEATURE_ROOTS
    if path.startswith("/api/v1/advertising/"):
        return False
    if path.startswith("/api/v1/properties/"):
        return url_name not in PROPERTY_DEFERRED_NAMES
    if path.startswith("/api/v1/profiles/"):
        return url_name not in PROFILE_DEFERRED_NAMES
    # Public test checkout starts a new financial operation, unlike callbacks.
    if path == "/api/v1/payments/paymob/test-checkout/":
        return False
    return True


class MvpScopeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        name = getattr(request.resolver_match, "url_name", None)
        scope = request.GET.get("workspace", request.GET.get("scope", ""))
        deferred_context = enabled() and request.path_info.startswith("/api/v1/") and (
            scope.split("/", 1)[0] in {"student", "company"}
            or bool(request.headers.get("X-Sukoon-Company-Id"))
            or bool(request.headers.get("X-Sukoon-Company-Role"))
        )
        if deferred_context or not allows_path(request.path_info, name, request.method):
            return JsonResponse({
                "detail": "This workflow is deferred for the MVP release.",
                "code": "mvp_feature_deferred",
            }, status=403)
        return None
