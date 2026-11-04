"""Run with Django SimpleTestCase; no database or provider is involved."""
from types import SimpleNamespace
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import path
from core_apps.common.mvp_scope import MvpScopeMiddleware, allows_path


def protected_view(request):
    raise AssertionError("Deferred view must never execute")


urlpatterns = [path("api/v1/features/v1/leases/", protected_view)]


@override_settings(SUKOON_MVP=True)
class MvpScopeTests(SimpleTestCase):
    def test_staff_entry_points_do_not_restore_deferred_finance_or_tenancy_reviews(self):
        for root in ('financials', 'reviews', 'review-cases', 'review-appeals',
                     'review-recovery', 'review-windows'):
            self.assertFalse(allows_path(f'/api/v1/admin/{root}/'))
        for root in ('support', 'properties', 'kyc', 'security'):
            self.assertTrue(allows_path(f'/api/v1/admin/{root}/'))

    def test_shared_endpoints_cannot_restore_deferred_workspace(self):
        middleware = MvpScopeMiddleware(lambda request: HttpResponse())
        for params in ({"workspace": "student"}, {"scope": "company/id/approver"}):
            request = RequestFactory().get("/api/v1/chat/lists/", params)
            request.resolver_match = SimpleNamespace(url_name=None)
            self.assertEqual(middleware.process_view(request, None, (), {}).status_code, 403)
        request = RequestFactory().get("/api/v1/chat/lists/", HTTP_X_SUKOON_COMPANY_ID="old-company")
        request.resolver_match = SimpleNamespace(url_name=None)
        self.assertEqual(middleware.process_view(request, None, (), {}).status_code, 403)

    @override_settings(
        ROOT_URLCONF=__name__, ALLOWED_HOSTS=["testserver"],
        MIDDLEWARE=["core_apps.common.mvp_scope.MvpScopeMiddleware"],
    )
    def test_http_dispatch_stops_before_deferred_view(self):
        response = self.client.post("/api/v1/features/v1/leases/", {})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "mvp_feature_deferred")

    def test_auth_discovery_inventory_viewings_and_chat_stay_available(self):
        for path in (
            "/api/v1/auth/login/", "/api/v1/profiles/my-account/",
            "/api/v1/properties/create/", "/api/v1/properties/saved/",
            "/api/v1/properties/visits/creation-receipt/",
            "/api/v1/chat/conversations/create/",
            "/api/v1/chat/messages/search/", "/api/v1/notifications/",
            "/api/v1/features/v1/search-alerts/",
            "/api/v1/features/v1/decision-notebook/",
            "/api/v1/features/v1/workspace-summary/",
        ):
            with self.subTest(path=path):
                self.assertTrue(allows_path(path))

    def test_deferred_workflow_never_reaches_the_view(self):
        middleware = MvpScopeMiddleware(lambda request: HttpResponse())
        for resource in (
            "tenancy-invitations", "leases", "terms-proposals",
            "rental-interests", "companies", "student-plans",
            "housing-groups", "reservation-holds", "subscriptions",
            "rental-center", "refund-requests", "unknown-future-workflow",
        ):
            for method in ("get", "post", "patch", "delete"):
                request = getattr(RequestFactory(), method)(
                    f"/api/v1/features/v1/{resource}/")
                request.resolver_match = SimpleNamespace(url_name=None)
                response = middleware.process_view(request, None, (), {})
                with self.subTest(resource=resource, method=method):
                    self.assertEqual(response.status_code, 403)
                    self.assertIn(b"mvp_feature_deferred", response.content)

    def test_public_reputation_remains_readable_without_enabling_review_writes(self):
        path = "/api/v1/features/v1/reviews/subjects/property/id/public-summary/"
        self.assertTrue(allows_path(path))
        self.assertFalse(allows_path(path, method="POST"))
        self.assertFalse(allows_path("/api/v1/properties/visits/id/review/", "property-visit-review-create", "POST"))

    def test_nested_property_and_profile_actions_cannot_bypass_scope(self):
        self.assertFalse(allows_path("/api/v1/properties/visits/id/post-visit-decision/", "post-visit-decision"))
        self.assertFalse(allows_path("/api/v1/profiles/contracts/", "tenant-contracts-list"))
        self.assertFalse(allows_path("/api/v1/payments/paymob/test-checkout/"))

    def test_existing_provider_callbacks_are_preserved(self):
        self.assertTrue(allows_path("/api/v1/payments/paymob/webhook/"))
        self.assertTrue(allows_path("/api/v1/payments/paymob/return/"))
        self.assertTrue(allows_path("/api/v1/features/v1/signing/provider-events/"))

    @override_settings(SUKOON_MVP=False)
    def test_switch_restores_original_routes(self):
        self.assertTrue(allows_path("/api/v1/features/v1/leases/"))
        self.assertTrue(allows_path("/api/v1/profiles/contracts/", "tenant-contracts-list"))
