"""Stable public imports for serializers.

Implementation modules separate domain responsibilities without changing routes.
"""

from django.contrib.auth import get_user_model
from djoser.serializers import UserCreatePasswordRetypeSerializer, UserSerializer
from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from core_apps.profiles.serializers import CloudinarySerializerField
from .journey import PrivateJourneySerializerMixin

from .serializers_parts.create_user_serializer import (
    User,
    CreateUserSerializer,
    CustomUserSerializer,
    CurrentUserSerializer,
    CompleteRegisterSerializer,
    GoogleAuthSerializer,
    AppleAuthSerializer,
    FacebookAuthSerializer,
)
from .serializers_parts.set_user_password_serializer import (
    UserDeleteSerializer,
    VerifyEmailSerializer,
    ResendOtpSerializer,
    SetUserPasswordSerializer,
)

# Preserve the existing public import surface, including compatibility seams.
__all__ = [
    'get_user_model',
    'UserCreatePasswordRetypeSerializer',
    'UserSerializer',
    'serializers',
    'PhoneNumberField',
    'CloudinarySerializerField',
    'PrivateJourneySerializerMixin',
    'User',
    'CreateUserSerializer',
    'CustomUserSerializer',
    'CurrentUserSerializer',
    'CompleteRegisterSerializer',
    'GoogleAuthSerializer',
    'AppleAuthSerializer',
    'FacebookAuthSerializer',
    'UserDeleteSerializer',
    'VerifyEmailSerializer',
    'ResendOtpSerializer',
    'SetUserPasswordSerializer',
]
