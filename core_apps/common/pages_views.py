import logging
from datetime import datetime, timezone

from django.http import Http404
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.renderers import GenericJsonRenderer
from .pages_serializers import PageContentSerializer

logger = logging.getLogger(__name__)

# * Default static copy for pages in English and Arabic
STATIC_PAGES_CONTENT = {
    "about-us": {
        "en": {
            "title": "About Us",
            "content": (
                "Sokoun is an innovative real estate rental and discovery platform designed "
                "to streamline property discovery, booking, and communications between owners and tenants."
            ),
        },
        "ar": {
            "title": "عن سكون",
            "content": (
                "سكون هي منصة عقارية مبتكرة لتأجير واستكشاف العقارات، تهدف إلى تسهيل البحث عن العقارات "
                "وحجز الزيارات والتواصل المباشر بين الملاك والمستأجرين."
            ),
        },
    },
    "privacy-policy": {
        "en": {
            "title": "Privacy Policy",
            "content": (
                "At Sokoun, we respect your privacy and are committed to protecting your personal data. "
                "This policy explains how we collect, store, and process your information when using our application."
            ),
        },
        "ar": {
            "title": "سياسة الخصوصية",
            "content": (
                "في سكون، نحن نحترم خصوصيتك ونلتزم بحماية بياناتك الشخصية. "
                "توضح هذه السياسة كيفية جمع بياناتك وتخزينها ومعالجتها عند استخدامك للتطبيق."
            ),
        },
    },
    "terms": {
        "en": {
            "title": "Terms and Conditions",
            "content": (
                "By accessing and using Sokoun, you agree to comply with our terms of service, "
                "including fair use, accurate listings, and respectful interactions."
            ),
        },
        "ar": {
            "title": "الشروط والأحكام",
            "content": (
                "باستخدامك لمنصة سكون، فإنك توافق على الالتزام بشروط وأحكام الخدمة، "
                "بما يشمل الاستخدام العادل ودقة بيانات العقارات والتعامل المحترم."
            ),
        },
    },
}

PAGE_LAST_UPDATED = datetime(2026, 9, 28, 0, 0, 0, tzinfo=timezone.utc)


class StaticPageAPIView(APIView):
    """
    Public read endpoint for static and legal content (About Us, Privacy Policy, Terms).
    Supports English ('en') and Arabic ('ar') via query parameter ?lang= or Accept-Language header.
    """

    permission_classes = [permissions.AllowAny]
    renderer_classes = [GenericJsonRenderer]
    serializer_class = PageContentSerializer

    slug: str = ""

    def get_slug(self) -> str:
        return self.slug or self.kwargs.get("slug", "")

    def get_language(self, request: Request) -> str:
        lang = request.query_params.get("lang") or request.query_params.get("language")
        if lang and lang.lower().startswith("ar"):
            return "ar"
        if lang and lang.lower().startswith("en"):
            return "en"
        accept_lang = request.headers.get("Accept-Language", "")
        if "ar" in accept_lang.lower():
            return "ar"
        return "en"

    def get(self, request: Request, *args, **kwargs) -> Response:
        slug = self.get_slug()
        if slug not in STATIC_PAGES_CONTENT:
            raise Http404(f"Page '{slug}' not found.")

        language = self.get_language(request)
        page_info = STATIC_PAGES_CONTENT[slug].get(
            language, STATIC_PAGES_CONTENT[slug]["en"]
        )

        data = {
            "slug": slug,
            "title": page_info["title"],
            "content": page_info["content"],
            "content_format": "plain_text",
            "language": language,
            "updated_at": PAGE_LAST_UPDATED,
        }
        serializer = self.serializer_class(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AboutUsPageAPIView(StaticPageAPIView):
    slug = "about-us"


class PrivacyPolicyPageAPIView(StaticPageAPIView):
    slug = "privacy-policy"


class TermsPageAPIView(StaticPageAPIView):
    slug = "terms"
