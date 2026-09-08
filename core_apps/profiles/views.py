import logging
from typing import List

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from core_apps.common.pagination import StandardResultsSetPagination
from core_apps.common.renderers import GenericJsonRenderer

from .models import Profile, UserSettings
from .serializers import (
    AccountSummaryScreenSerializer,
    MyAccountScreenSerializer,
    ProfileEditSerializer,
    ProfileSerializer,
    UpdateProfileSerializer,
    UserSettingsSerializer,
)
from .services import ProfileService

logger = logging.getLogger(__name__)
User = get_user_model()


class ProfileListAPIView(generics.ListAPIView):
    serializer_class = ProfileSerializer
    renderer_classes = [GenericJsonRenderer]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["user__first_name", "user__last_name"]
    filterset_fields = ["gender"]

    def get_queryset(self) -> List[Profile]:
        return Profile.objects.exclude(user__is_staff=True).exclude(
            user__is_superuser=True
        )


class ProfileDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    renderer_classes = [GenericJsonRenderer]

    def get_queryset(self) -> QuerySet:
        return Profile.objects.select_related("user").all()

    def get_object(self) -> Profile:
        try:
            return self.get_queryset().get(user=self.request.user)
        except Profile.DoesNotExist:
            raise Http404("Profile is Not found for this user!")


class ProfileUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UpdateProfileSerializer
    renderer_classes = [GenericJsonRenderer]

    def get_queryset(self) -> None:
        return Profile.objects.none()

    def get_object(self) -> Profile:
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def perform_update(self, serializer: UpdateProfileSerializer):
        user_data = serializer.validated_data.pop("user", {})
        profile = serializer.save()
        User.objects.filter(id=self.request.user.id).update(**user_data)
        return profile


# * =========================================================================
# * Mobile Screen Views
# * =========================================================================


class MyAccountDetailAPIView(generics.RetrieveAPIView):
    """
    Screen 1: 'حسابي' (My Account).

    Returns profile card, statistics (saved, visits, reviews),
    action menu items, and account details.
    """

    serializer_class = MyAccountScreenSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        data = ProfileService.get_my_account_data(request.user)
        serializer = self.get_serializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AccountSummaryDetailAPIView(generics.RetrieveAPIView):
    """
    Screen 2: 'ملخص الحساب' (Account Summary).

    Returns hero profile card with 80% completion progress,
    identity verification status, statistics, and navigation shortcuts.
    """

    serializer_class = AccountSummaryScreenSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        data = ProfileService.get_account_summary_data(request.user)
        serializer = self.get_serializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileEditAPIView(generics.RetrieveUpdateAPIView):
    """
    Screen 3: 'تعديل الملف' (Edit Profile).

    GET: Returns prefilled values for avatar, profile_image, full_name, phone_number,
    masked_phone_number, email, birth_date, birth_date_label, gender, and gender_label.

    PUT/PATCH: Updates profile fields, user profile image, and user's full name atomically.
    Accepts application/json, multipart/form-data (for image file upload), or application/x-www-form-urlencoded.
    Profile image can be uploaded via 'avatar', 'profile_image', or 'image' field.

    Request Body Example (PATCH/PUT - Multipart Form or JSON):
    {
        "full_name": "محمد أحمد",
        "phone_number": "+201012345432",
        "birth_date": "1995-03-15",
        "gender": "male",
        "avatar": "<image_file_or_data_uri>"
    }
    """

    serializer_class = ProfileEditSerializer
    renderer_classes = [GenericJsonRenderer]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> Profile:
        profile, _ = Profile.objects.select_related("user").get_or_create(
            user=self.request.user
        )
        return profile

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        profile = ProfileService.update_user_profile(
            user=request.user, validated_data=serializer.validated_data
        )

        response_serializer = self.get_serializer(profile)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class UserSettingsAPIView(generics.RetrieveUpdateAPIView):
    """
    Screen: 'الإعدادات والخصوصية' (Settings & Privacy).

    GET: Returns user notification and privacy settings with grouped UI sections.

    PUT/PATCH: Updates user notification and privacy settings.

    Request Body Example (PATCH / PUT):
    {
        "visit_notifications": true,
        "new_properties_in_area": true,
        "owner_messages": true,
        "promotions_and_updates": false,
        "share_location_for_search": true,
        "show_profile_in_search": false
    }

    Nested payload is also supported:
    {
        "notifications": {
            "visit_notifications": false
        },
        "privacy": {
            "show_profile_in_search": true
        }
    }
    """

    serializer_class = UserSettingsSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> UserSettings:
        return ProfileService.get_user_settings(self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        settings_obj = ProfileService.update_user_settings(
            user=request.user, validated_data=serializer.validated_data
        )

        response_serializer = self.get_serializer(settings_obj)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
