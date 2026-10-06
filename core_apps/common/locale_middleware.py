from typing import Callable
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils import translation
from django.utils.cache import patch_vary_headers


def is_mobile_request(request: HttpRequest) -> bool:
    """
    Determines whether the incoming request targets a mobile API endpoint.
    All /api/v1/* endpoints EXCEPT /api/v1/admin/ and Django admin are mobile APIs.
    """
    path = request.path_info or request.path

    # * Exclude Django Admin
    admin_url = getattr(settings, "ADMIN_URL", "admin/")
    if not admin_url.startswith("/"):
        admin_url = "/" + admin_url
    if path.startswith(admin_url):
        return False

    # * Exclude Web Frontend Admin APIs
    if path.startswith("/api/v1/admin/"):
        return False

    # * Mobile APIs are versioned under /api/v1/
    return path.startswith("/api/v1/")


def resolve_request_language(request: HttpRequest) -> str:
    """
    Resolves the language ('ar' or 'en') for the mobile request.
    Supports ?lang= query param and Accept-Language header.
    Defaults to 'en' if not provided or unspecified.
    """
    # ? Query param override for flexibility and testing
    lang_param = request.GET.get("lang") or request.GET.get("language")
    if lang_param:
        clean = lang_param.strip().lower()
        if clean.startswith("ar"):
            return "ar"
        if clean.startswith("en"):
            return "en"

    # ? Parse Accept-Language header (e.g. 'ar', 'ar-EG', 'ar,en;q=0.9', 'en-US,en;q=0.5')
    accept_language = request.headers.get("Accept-Language") or request.META.get(
        "HTTP_ACCEPT_LANGUAGE", ""
    )
    if accept_language:
        # Check standard languages
        parts = [p.strip().split(";")[0].lower() for p in accept_language.split(",") if p.strip()]
        for part in parts:
            if part.startswith("ar"):
                return "ar"
            if part.startswith("en"):
                return "en"

    return "en"


class MobileLocaleMiddleware:
    """
    Middleware that handles localization (Accept-Language: ar / en)
    strictly for mobile-consumed API endpoints (/api/v1/* excluding /api/v1/admin/).
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not is_mobile_request(request):
            return self.get_response(request)

        language = resolve_request_language(request)
        translation.activate(language)
        request.LANGUAGE_CODE = language

        try:
            response = self.get_response(request)
            response["Content-Language"] = language
            patch_vary_headers(response, ["Accept-Language"])
            return response
        finally:
            translation.deactivate()
