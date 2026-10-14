"""Stable public imports for views.

Implementation modules separate domain responsibilities without changing routes.
"""

import logging
from typing import Optional
from django.conf import settings
from django.shortcuts import render
from django.views import View
from djoser.social.views import ProviderAuthView
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from core_apps.common.renderers import GenericJsonRenderer
from .journey import canonical_user
from .token_serializers import CanonicalTokenObtainPairSerializer
from core_apps.users.serializers import (
    CompleteRegisterSerializer,
    CreateUserSerializer,
    GoogleAuthSerializer,
    AppleAuthSerializer,
    FacebookAuthSerializer,
    SetUserPasswordSerializer,
    UserDeleteSerializer,
    VerifyEmailSerializer,
    ResendOtpSerializer,
)
from core_apps.users.services.social_auth_service import (
    authenticate_google,
    authenticate_apple,
    authenticate_facebook,
)
from core_apps.users.services.user_service import (
    change_user_password,
    complete_user_registration,
    delete_user_account,
    register_user,
)
from core_apps.users.services.otp_service import (
    verify_email_otp,
    resend_verification_otp,
)

from .views_parts.set_auth_cookies import (
    logger,
    set_auth_cookies,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomProviderAuthView,
    LogoutAPIView,
    _issue_jwt,
    _user_payload,
)
from .views_parts.user_delete_apiview import (
    GoogleAuthView,
    AppleAuthView,
    FacebookAuthView,
    PasswordResetConfirmView,
    UserDeleteAPIView,
)
from .views_parts.verify_email_apiview import (
    UserRegisterAPIView,
    VerifyEmailAPIView,
    ResendOtpAPIView,
    CompleteRegisterAPIView,
    SetPasswordAPIView,
)
