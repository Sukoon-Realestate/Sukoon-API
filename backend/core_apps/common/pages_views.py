import logging

from django.http import Http404
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.renderers import GenericJsonRenderer
from .pages_serializers import PageContentSerializer
from .content_models import PublicContentPage

logger = logging.getLogger(__name__)


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
        from .locale_middleware import resolve_request_language
        return resolve_request_language(request)

    def get(self, request: Request, *args, **kwargs) -> Response:
        slug = self.get_slug()
        page_info = PublicContentPage.objects.filter(slug=slug, active=True).first()
        if page_info is None:
            raise Http404("Page not found.")
        language = self.get_language(request)

        data = {
            "slug": slug,
            "title": getattr(page_info, f"title_{language}"),
            "content": getattr(page_info, f"content_{language}"),
            "content_format": "plain_text",
            "language": language,
            "updated_at": page_info.updated_at,
            "revision": page_info.revision,
        }
        serializer = self.serializer_class(data)
        response = Response(serializer.data, status=status.HTTP_200_OK)
        response["Cache-Control"] = "public, max-age=0, must-revalidate"
        response["Content-Language"] = language
        response["Vary"] = "Accept-Language"
        return response


class AboutUsPageAPIView(StaticPageAPIView):
    slug = "about-us"


class PrivacyPolicyPageAPIView(StaticPageAPIView):
    slug = "privacy-policy"


class TermsPageAPIView(StaticPageAPIView):
    slug = "terms"
