"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# ! Initialize Django settings BEFORE importing anything that touches models/consumers
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django_asgi_app = get_asgi_application()

from django.conf import settings  # noqa: E402

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

from core_apps.common.routing import websocket_urlpatterns  # noqa: E402
from core_apps.common.ws_auth import JWTCookieAuthMiddleware  # noqa: E402

_ws_app = JWTCookieAuthMiddleware(URLRouter(websocket_urlpatterns))

# ? Origin validator prevents cross-origin WS connections; skip in dev where ALLOWED_HOSTS
# ? contains bare hostnames that don't match Postman/browser tool origin headers with ports.
if not settings.DEBUG:
    _ws_app = AllowedHostsOriginValidator(_ws_app)

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": _ws_app,
    }
)
