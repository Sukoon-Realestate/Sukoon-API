"""Public, versioned viewer shell; private tour bytes stay behind session grants."""

import re
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_safe

CSP = (
    "default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; "
    "connect-src 'self'; font-src 'self'; worker-src 'self' blob:; "
    "frame-src 'none'; frame-ancestors 'self'; base-uri 'none'; "
    "form-action 'none'; object-src 'none'"
)


@require_safe
@xframe_options_sameorigin
def viewer(request, filename=None):
    if filename is not None and not re.fullmatch(
        r"[A-Za-z0-9_-]+\.(?:js|css|wasm)", filename
    ):
        raise Http404
    root = Path(settings.VIRTUAL_TOUR_VIEWER_ROOT).resolve()
    target = root / "assets" / filename if filename else root / "index.html"
    if not target.is_file() or root not in target.resolve().parents:
        raise Http404
    response = FileResponse(target.open("rb"))
    response["Content-Security-Policy"] = CSP
    response["Referrer-Policy"] = "no-referrer"
    response["X-Content-Type-Options"] = "nosniff"
    response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response["Cache-Control"] = (
        "public, max-age=31536000, immutable" if filename else "no-cache"
    )
    return response
