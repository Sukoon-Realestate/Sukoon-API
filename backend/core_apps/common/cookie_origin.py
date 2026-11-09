"""A1-08: origin proof for unsafe requests that rely on ambient auth cookies.

SameSite=Lax already keeps cookies off most cross-site writes. This adds an explicit
server-side check for the remaining cases (same-site hostile subdomains, relaxed future
cookie settings): when a browser sends an Origin header with a cookie-authenticated
unsafe request, it must be this host or a configured trusted origin. Bearer-header
clients (mobile, the web admin) and signed provider callbacks do not use this path.
"""

from django.conf import settings
from django.core.exceptions import DisallowedHost
from rest_framework.exceptions import PermissionDenied

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})


def trusted_origins(request):
    allowed = set(getattr(settings, "CSRF_TRUSTED_ORIGINS", []) or [])
    allowed |= set(getattr(settings, "COOKIE_TRUSTED_ORIGINS", []) or [])
    try:
        allowed.add(f"{request.scheme}://{request.get_host()}")
    except DisallowedHost:
        pass
    return allowed


def require_cookie_origin(request):
    """Raise 403 when a cookie-authenticated unsafe request carries a foreign Origin."""
    if not getattr(settings, "COOKIE_ORIGIN_ENFORCEMENT", True):
        return
    if request.method in SAFE_METHODS:
        return
    origin = request.META.get("HTTP_ORIGIN")
    if origin is None:
        return
    if origin == "null" or origin not in trusted_origins(request):
        raise PermissionDenied(
            "This request's origin is not allowed to use session cookies.",
            code="cookie_origin_rejected",
        )
