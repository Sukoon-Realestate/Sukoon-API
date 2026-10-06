import json
import pytest
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory

from core_apps.common.locale_middleware import (
    MobileLocaleMiddleware,
    is_mobile_request,
    resolve_request_language,
)
from core_apps.common.renderers import GenericJsonRenderer, custom_exception_handler
from core_apps.common.translation import (
    translate_choice,
    translate_field_label,
    translate_message,
    translate_tag,
)

User = get_user_model()


class TestMobileLocaleDetection:
    """Tests for mobile request detection and language resolution."""

    def test_is_mobile_request_detection(self):
        rf = RequestFactory()

        # * Mobile endpoints under /api/v1/
        assert is_mobile_request(rf.get("/api/v1/properties/")) is True
        assert is_mobile_request(rf.get("/api/v1/auth/login/")) is True
        assert is_mobile_request(rf.get("/api/v1/notifications/")) is True
        assert is_mobile_request(rf.get("/api/v1/support/tickets/")) is True
        assert is_mobile_request(rf.get("/api/v1/pages/about-us/")) is True

        # * Non-mobile endpoints
        assert is_mobile_request(rf.get("/api/v1/admin/dashboard/")) is False
        assert is_mobile_request(rf.get("/api/v1/admin/properties/")) is False
        assert is_mobile_request(rf.get("/admin/")) is False
        assert is_mobile_request(rf.get("/super-secret-admin/")) is False
        assert is_mobile_request(rf.get("/schema-redoc/")) is False

    def test_resolve_request_language_header(self):
        rf = RequestFactory()

        # * Arabic Accept-Language
        req_ar = rf.get("/api/v1/properties/", HTTP_ACCEPT_LANGUAGE="ar")
        assert resolve_request_language(req_ar) == "ar"

        req_ar_eg = rf.get("/api/v1/properties/", HTTP_ACCEPT_LANGUAGE="ar-EG,ar;q=0.9,en;q=0.8")
        assert resolve_request_language(req_ar_eg) == "ar"

        # * English Accept-Language
        req_en = rf.get("/api/v1/properties/", HTTP_ACCEPT_LANGUAGE="en")
        assert resolve_request_language(req_en) == "en"

        req_en_us = rf.get("/api/v1/properties/", HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9")
        assert resolve_request_language(req_en_us) == "en"

        # * Missing header defaults to English
        req_none = rf.get("/api/v1/properties/")
        assert resolve_request_language(req_none) == "en"

    def test_resolve_request_language_query_param(self):
        rf = RequestFactory()

        # * Query parameter overrides / provides language
        req_param_ar = rf.get("/api/v1/properties/?lang=ar")
        assert resolve_request_language(req_param_ar) == "ar"

        req_param_en = rf.get("/api/v1/properties/?lang=en", HTTP_ACCEPT_LANGUAGE="ar")
        assert resolve_request_language(req_param_en) == "en"


class TestMobileLocaleMiddleware:
    """Tests for MobileLocaleMiddleware execution and headers."""

    def test_middleware_sets_content_language_for_mobile_ar(self):
        rf = RequestFactory()
        req = rf.get("/api/v1/properties/", HTTP_ACCEPT_LANGUAGE="ar")

        def dummy_view(request):
            return HttpResponse("OK")

        middleware = MobileLocaleMiddleware(dummy_view)
        response = middleware(req)

        assert response.status_code == 200
        assert response["Content-Language"] == "ar"
        assert "Accept-Language" in response["Vary"]

    def test_middleware_sets_content_language_for_mobile_en(self):
        rf = RequestFactory()
        req = rf.get("/api/v1/properties/", HTTP_ACCEPT_LANGUAGE="en")

        def dummy_view(request):
            return HttpResponse("OK")

        middleware = MobileLocaleMiddleware(dummy_view)
        response = middleware(req)

        assert response.status_code == 200
        assert response["Content-Language"] == "en"
        assert "Accept-Language" in response["Vary"]

    def test_middleware_ignores_admin_and_frontend_requests(self):
        rf = RequestFactory()
        req = rf.get("/api/v1/admin/dashboard/", HTTP_ACCEPT_LANGUAGE="ar")

        def dummy_view(request):
            return HttpResponse("OK")

        middleware = MobileLocaleMiddleware(dummy_view)
        response = middleware(req)

        assert response.status_code == 200
        assert "Content-Language" not in response


class TestTranslationCatalog:
    """Unit tests for the translation helpers."""

    def test_translate_message_bidirectional(self):
        # * English to Arabic
        assert translate_message("Created successfully.", "ar") == "تم الإنشاء بنجاح."
        assert translate_message("Logged in Successfully", "ar") == "تم تسجيل الدخول بنجاح."
        assert translate_message("Invalid credentials.", "ar") == "بيانات الدخول غير صحيحة."
        assert (
            translate_message("Marked 5 notifications as read.", "ar")
            == "تم تحديد 5 إشعارات كمقروءة."
        )

        # * Arabic to English
        assert translate_message("تم تغيير كلمة المرور بنجاح", "en") == "Password changed successfully."
        assert translate_message("تم الإنشاء بنجاح.", "en") == "Created successfully."

    def test_translate_field_label(self):
        assert translate_field_label("Email", "ar") == "البريد الإلكتروني"
        assert translate_field_label("Password", "ar") == "كلمة المرور"
        assert translate_field_label("Email", "en") == "Email"

    def test_translate_tag_and_choice(self):
        assert translate_tag("عائلات", "en") == "Families"
        assert translate_tag("ممنوع التدخين", "en") == "No Smoking"
        assert translate_tag("No Smoking", "ar") == "ممنوع التدخين"

        assert translate_choice("daily", "ar") == "يومي"
        assert translate_choice("daily", "en") == "Daily"


class TestGenericJsonRendererLocalization:
    """Integration tests for GenericJsonRenderer translation."""

    def test_renderer_translates_success_message_to_arabic(self):
        factory = APIRequestFactory()
        request = factory.post("/api/v1/auth/login/", HTTP_ACCEPT_LANGUAGE="ar")
        request.LANGUAGE_CODE = "ar"

        response = Response({"message": "Logged in Successfully", "token": "xyz"}, status=200)
        renderer = GenericJsonRenderer()

        rendered = renderer.render(
            response.data,
            renderer_context={"response": response, "request": request},
        )
        data = json.loads(rendered)

        assert data["message"] == "تم تسجيل الدخول بنجاح."
        assert data["data"] == {"token": "xyz"}

    def test_renderer_translates_arabic_success_message_to_english(self):
        factory = APIRequestFactory()
        request = factory.post("/api/v1/auth/set-password/", HTTP_ACCEPT_LANGUAGE="en")
        request.LANGUAGE_CODE = "en"

        response = Response({"message": "تم تغيير كلمة المرور بنجاح"}, status=200)
        renderer = GenericJsonRenderer()

        rendered = renderer.render(
            response.data,
            renderer_context={"response": response, "request": request},
        )
        data = json.loads(rendered)

        assert data["message"] == "Password changed successfully."

    def test_renderer_translates_field_errors_to_arabic(self):
        factory = APIRequestFactory()
        request = factory.post("/api/v1/auth/login/", HTTP_ACCEPT_LANGUAGE="ar")
        request.LANGUAGE_CODE = "ar"

        response = Response({"email": ["This field is required."]}, status=400)
        renderer = GenericJsonRenderer()

        rendered = renderer.render(
            response.data,
            renderer_context={"response": response, "request": request},
        )
        data = json.loads(rendered)

        assert "البريد الإلكتروني" in data["message"]
        assert "هذا الحقل مطلوب." in data["message"]

    def test_custom_exception_handler_with_arabic_request(self):
        factory = APIRequestFactory()
        request = factory.get("/api/v1/properties/", HTTP_ACCEPT_LANGUAGE="ar")
        request.LANGUAGE_CODE = "ar"

        response = custom_exception_handler(
            NotAuthenticated(),
            {"request": request, "view": None},
        )

        assert response.status_code == 401
        assert "بيانات الدخول" in response.data["message"] or "غير مصرح" in response.data["message"]


@pytest.mark.django_db
class TestFilterOptionsLocalizationAPI:
    """Integration test for property filter options with Accept-Language."""

    def test_filter_options_returns_english_when_requested(self, auth_client):
        url = reverse("property-filter-options")
        response = auth_client.get(url, HTTP_ACCEPT_LANGUAGE="en")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]

        # * Price periods should have English labels
        daily = next(p for p in data["price_periods"] if p["value"] == "daily")
        assert daily["label"] == "Daily"

        # * Suitable for should have English labels
        families = next(s for s in data["suitable_for"] if s["value"] == "families")
        assert families["label"] == "Families"

        # * Amenities should have English labels
        wifi = next(a for a in data["amenities"] if a["value"] == "wifi")
        assert wifi["label"] == "WiFi"

    def test_filter_options_returns_arabic_by_default_or_when_requested(self, auth_client):
        url = reverse("property-filter-options")
        response = auth_client.get(url, HTTP_ACCEPT_LANGUAGE="ar")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]

        daily = next(p for p in data["price_periods"] if p["value"] == "daily")
        assert daily["label"] == "يومي"

        families = next(s for s in data["suitable_for"] if s["value"] == "families")
        assert families["label"] == "عائلات"
