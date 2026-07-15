import logging
from typing import Optional
from django.conf import settings
from djoser.social.views import ProviderAuthView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


logger = logging.getLogger(__name__)


def set_auth_cookies(
    response: Response, access_token: str, refresh_token: Optional[str]
) -> None:
    """
    ? Sets access, refresh, and logged_in cookies on the response.

    Cookie settings (path, secure, httponly, samesite, max_age) come from settings.

    ! Modifies the response object directly.
    """

    # * Access token settings
    access_token_lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()

    cookie_settings = {
        "path": settings.COOKIE_PATH,
        "secure": settings.COOKIE_SECURE,
        "httponly": settings.COOKIE_HTTPONLY,
        "samesite": settings.COOKIE_SAMESITE,
        "max_age": access_token_lifetime,
    }

    response.set_cookie("access", access_token, **cookie_settings)

    # * Refresh token settings
    if refresh_token:
        refresh_token_lifetime = settings.SIMPLE_JWT[
            "REFRESH_TOKEN_LIFETIME"
        ].total_seconds()

        refresh_token_settings = cookie_settings.copy()
        refresh_token_settings["max_age"] = refresh_token_lifetime

        response.set_cookie("refresh", refresh_token, **refresh_token_settings)

    # * Logged in cookie settings
    logged_in_cookie_settings = cookie_settings.copy()

    logged_in_cookie_settings["httponly"] = False

    response.set_cookie("logged_in", "true", **logged_in_cookie_settings)


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        token_res = super().post(request, *args, **kwargs)

        if token_res.status_code == status.HTTP_200_OK:
            access_token = token_res.data.get("access")
            refresh_token = token_res.data.get("refresh")

            if access_token and refresh_token:
                set_auth_cookies(token_res, access_token, refresh_token)

                # * remove the access and refresh tokens from the response body
                token_res.data.pop("access", None)
                token_res.data.pop("refresh", None)

                token_res.data["message"] = "Logged in Successfully"

            else:
                token_res.data["message"] = "Login Failure"
                logger.error(
                    "Access or Refresh Tokens are not found in the Login Response data!"
                )

        return token_res


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        refresh_token = request.COOKIES.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.data["refresh"] = refresh_token
        refresh_res = super().post(request, *args, **kwargs)

        if refresh_res.status_code == status.HTTP_200_OK:
            access_token = refresh_res.data.get("access")
            refresh_token = refresh_res.data.get("refresh")

            if access_token and refresh_token:
                set_auth_cookies(refresh_res, access_token, refresh_token)

                refresh_res.data.pop("access", None)
                refresh_res.data.pop("refresh", None)

                refresh_res["message"] = "Token Refreshed Successfully"
            else:
                refresh_res["message"] = "Token Refresh Failure"
                logger.error("Access or Refresh Tokens missing from Refresh Response.")

        return refresh_res


class CustomProviderAuthView(ProviderAuthView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        provider_res = super().post(request, *args, **kwargs)

        if provider_res.status_code == status.HTTP_201_CREATED:
            access_token = provider_res.data.get("access")
            refresh_token = provider_res.data.get("refresh")

            set_auth_cookies(provider_res, access_token, refresh_token)

            provider_res.data.pop("access", None)
            provider_res.data.pop("refresh", None)

            provider_res.data["message"] = "Logged in Successfully"
        else:
            provider_res.data["message"] = (
                "Access or refresh token not found in provider response"
            )
            logger.error("Access or refresh token not found in provider response data")

        return provider_res


class LogoutAPIView(APIView):
    def post(self, request: Request, *args, **kwargs) -> Response:

        response = Response(status=status.HTTP_204_NO_CONTENT)

        response.delete_cookie("access")
        response.delete_cookie("refresh")
        response.delete_cookie("logged_in")

        return response
