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
    path = getattr(request, "path_info", "") or getattr(request, "path", "")

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
    return path.startswith("/api/v1/") or "/api/v1/" in path or path.startswith("/advertising/")


def resolve_request_language(request: HttpRequest) -> str:
    """
    Resolves the language ('ar' or 'en') for the mobile request.
    Supports ?lang= query param and Accept-Language header (including q-factor weights).
    Defaults to 'en' if not provided or unspecified.
    """
    # ? Query param override for flexibility and testing
    params = getattr(request, "query_params", None) or getattr(request, "GET", {})
    lang_param = params.get("lang") or params.get("language")
    if lang_param:
        clean = lang_param.strip().lower()
        if clean.startswith("ar"):
            return "ar"
        if clean.startswith("en"):
            return "en"

    # ? Parse Accept-Language header
    accept_language = ""
    if hasattr(request, "headers") and hasattr(request.headers, "get"):
        accept_language = request.headers.get("Accept-Language") or request.headers.get("accept-language") or ""
    if not accept_language and hasattr(request, "META"):
        accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")

    if accept_language:
        weighted = []
        for part in accept_language.split(","):
            part = part.strip()
            if not part:
                continue
            subparts = part.split(";")
            lang_tag = subparts[0].strip().lower()
            q = 1.0
            for param in subparts[1:]:
                param = param.strip()
                if param.startswith("q="):
                    try:
                        q = float(param[2:])
                    except ValueError:
                        pass
            if 0 < q <= 1:
                weighted.append((q, lang_tag))

        weighted.sort(key=lambda x: x[0], reverse=True)
        for _, tag in weighted:
            if tag.startswith("ar"):
                return "ar"
            if tag.startswith("en"):
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
