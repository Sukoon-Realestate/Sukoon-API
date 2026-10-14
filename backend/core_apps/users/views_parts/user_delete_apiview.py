"""Views: user delete apiview."""

from django.conf import settings
from django.shortcuts import render
from django.views import View
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.users.serializers import (
    GoogleAuthSerializer,
    AppleAuthSerializer,
    FacebookAuthSerializer,
    UserDeleteSerializer,
)
from core_apps.users.services.social_auth_service import (
    authenticate_google,
    authenticate_apple,
    authenticate_facebook,
)
from core_apps.users.services.user_service import delete_user_account
from .set_auth_cookies import logger, set_auth_cookies, _issue_jwt, _user_payload


class GoogleAuthView(APIView):
    """Sign in or register via a Google ID token obtained by the client."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = authenticate_google(serializer.validated_data["token"])
        except ValidationError as exc:
            logger.warning("Google auth failed: %s", exc.detail)
            return Response(
                {"detail": exc.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tokens = _issue_jwt(user)
        response = Response(
            {
                "message": "Logged in Successfully",
                "user": _user_payload(user),
            },
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, tokens["access"], tokens["refresh"])
        return response


class AppleAuthView(APIView):
    """Sign in or register via an Apple identity token obtained by the client."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = AppleAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            user = authenticate_apple(
                data["token"],
                data.get("first_name", ""),
                data.get("last_name", ""),
            )
        except ValidationError as exc:
            logger.warning("Apple auth failed: %s", exc.detail)
            return Response(
                {"detail": exc.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tokens = _issue_jwt(user)
        response = Response(
            {
                "message": "Logged in Successfully",
                "user": _user_payload(user),
            },
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, tokens["access"], tokens["refresh"])
        return response


class FacebookAuthView(APIView):
    """Sign in or register via a Facebook access token obtained by the client."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = FacebookAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = authenticate_facebook(serializer.validated_data["token"])
        except ValidationError as exc:
            logger.warning("Facebook auth failed: %s", exc.detail)
            return Response(
                {"detail": exc.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tokens = _issue_jwt(user)
        response = Response(
            {
                "message": "Logged in Successfully",
                "user": _user_payload(user),
            },
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, tokens["access"], tokens["refresh"])
        return response


class PasswordResetConfirmView(View):
    """
    Renders the custom password reset confirmation page.
    """

    def get(self, request, uid, token):
        context = {
            "uid": uid,
            "token": token,
        }
        return render(request, "password_reset_confirm.html", context)


class UserDeleteAPIView(generics.DestroyAPIView):
    """
    Delete the authenticated user's account permanently.

    Cascades deletion to Profile, UserSettings, SocialAccount,
    Properties, Visits, Reviews, Saved Properties, Favorites, and Ratings.
    Also clears authentication cookies.

    Supports both DELETE and POST methods.
    Optional payload:
    {
        "password": "current_password",
        "reason": "optional reason for deletion"
    }
    """

    serializer_class = UserDeleteSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        delete_user_account(instance)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        # * Validate serializer input if payload is provided
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance = self.get_object()
        self.perform_destroy(instance)

        response = Response(status=status.HTTP_200_OK)

        # * Clear authentication cookies
        response.delete_cookie("access", path=settings.COOKIE_PATH)
        response.delete_cookie("refresh", path=settings.COOKIE_PATH)
        response.delete_cookie("logged_in", path=settings.COOKIE_PATH)

        return response

    def post(self, request: Request, *args, **kwargs) -> Response:
        """Allow POST method as an alternative to DELETE for mobile/web clients."""
        return self.destroy(request, *args, **kwargs)
