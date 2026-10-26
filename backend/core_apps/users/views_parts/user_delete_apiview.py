"""Views: user delete apiview."""

from django.conf import settings
from django.shortcuts import render
from django.views import View
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.users.serializers import (
    GoogleAuthSerializer,
    AppleAuthSerializer,
    FacebookAuthSerializer,
)
from core_apps.users.services.social_auth_service import (
    authenticate_google,
    authenticate_apple,
    authenticate_facebook,
)
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


class UserDeleteAPIView(APIView):
    """Retired destructive route: clients must use the reviewed account request."""

    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]

    def delete(self, request):
        return Response({
            "message": "راجع طلب حذف الحساب من إعدادات الحساب. / Use the account closure review in account settings.",
            "code": "account_closure_review_required",
        }, status=status.HTTP_409_CONFLICT)

    post = delete
