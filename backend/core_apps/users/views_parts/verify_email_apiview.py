"""Views: verify email apiview."""

from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from core_apps.common.renderers import GenericJsonRenderer
from ..journey import canonical_user
from core_apps.users.serializers import (
    CompleteRegisterSerializer,
    CreateUserSerializer,
    SetUserPasswordSerializer,
    VerifyEmailSerializer,
    ResendOtpSerializer,
)
from core_apps.users.services.user_service import (
    change_user_password,
    complete_user_registration,
    register_user,
)
from core_apps.users.services.otp_service import (
    verify_email_otp,
    resend_verification_otp,
)
from .set_auth_cookies import set_auth_cookies, _issue_jwt


class UserRegisterAPIView(APIView):
    """
    Register a new user account and dispatch an email verification OTP.

    request.body example:
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password": "StrongPassword123!",
        "re_password": "StrongPassword123!",
        "birth_date": "1995-05-15",
        "phone_number": "+201234567890"
    }
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = register_user(serializer.validated_data)

        return Response(
            {
                "message": "Registration successful. A verification code has been sent to your email.",
                "user": canonical_user(user),
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailAPIView(APIView):
    """
    Verify a user's email address using the 6-digit OTP received via email.
    Upon successful verification, sets authentication cookies.

    request.body example:
    {
        "email": "john.doe@example.com",
        "otp": "123456"
    }
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = verify_email_otp(
            email=serializer.validated_data["email"],
            otp=serializer.validated_data["otp"],
        )

        tokens = _issue_jwt(user)
        response = Response(
            {
                "message": "Email verified successfully.",
                "user": canonical_user(user),
            },
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, tokens["access"], tokens["refresh"])
        return response


class ResendOtpAPIView(APIView):
    """
    Resend a new email verification OTP to an unverified user.

    request.body example:
    {
        "email": "john.doe@example.com"
    }
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = ResendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resend_verification_otp(serializer.validated_data["email"])

        return Response(
            {
                "message": "A new verification code has been sent to your email.",
            },
            status=status.HTTP_200_OK,
        )


class CompleteRegisterAPIView(APIView):
    """
    Complete registration by supplying missing national ID and identity documents.
    Multipart form-data endpoint for authenticated users.

    request.body (multipart):
    - national_id: "12345678901234"
    - front_id_image: <file>
    - back_id_image: <file>
    - selfie_image: <file> (optional)
    """

    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = CompleteRegisterSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = complete_user_registration(
            user=request.user,
            validated_data=serializer.validated_data,
        )

        return Response(result, status=status.HTTP_200_OK)


class SetPasswordAPIView(generics.GenericAPIView):
    """
    POST auth/users/set_password/
    Allows authenticated users to change their password.
    Keeps the current session/cookie valid.

    Request Body:
    {
        "current_password": "OldPassword123!",
        "new_password": "NewPassword123!",
        "re_new_password": "NewPassword123!"
    }
    """

    permission_classes = [IsAuthenticated]
    renderer_classes = [GenericJsonRenderer]
    serializer_class = SetUserPasswordSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        change_user_password(
            user=request.user,
            current_password=serializer.validated_data["current_password"],
            new_password=serializer.validated_data["new_password"],
        )

        return Response(
            {"message": "تم تغيير كلمة المرور بنجاح", "data": {}},
            status=status.HTTP_200_OK,
        )
