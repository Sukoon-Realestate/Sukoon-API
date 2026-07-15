import logging
from http.cookies import SimpleCookie

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)
User = get_user_model()


@database_sync_to_async
def _get_user(user_id):
    # ? DB access must be wrapped for the async consumer context
    try:
        return User.objects.get(id=user_id)
    except (User.DoesNotExist, ValueError, TypeError):
        return AnonymousUser()


class JWTCookieAuthMiddleware(BaseMiddleware):
    """Authenticate a WebSocket from the JWT stored in the access cookie.

    Mirrors the contract of core_apps.common.cookie_auth.CookieAuthentication:
    the access token lives in the cookie named ``settings.COOKIE_NAME`` and the
    user id is carried in the ``user_id`` claim.
    """

    async def __call__(self, scope, receive, send):
        from django.conf import settings

        scope["user"] = AnonymousUser()
        raw_token = self._token_from_scope(scope, settings.COOKIE_NAME)

        if raw_token:
            try:
                validated = AccessToken(raw_token)
                scope["user"] = await _get_user(validated["user_id"])
            except (TokenError, KeyError) as e:
                # ! Invalid/expired token -> stays anonymous; consumer decides to reject
                logger.error(f"WS token validation error: {e}")

        return await super().__call__(scope, receive, send)

    @staticmethod
    def _token_from_scope(scope, cookie_name):
        headers = dict(scope.get("headers", []))
        cookie_header = headers.get(b"cookie")
        if not cookie_header:
            return None
        try:
            cookies = SimpleCookie()
            cookies.load(cookie_header.decode())
            morsel = cookies.get(cookie_name)
            return morsel.value if morsel else None
        except UnicodeDecodeError as e:
            logger.error(f"WS cookie decode error: {e}")
            return None
