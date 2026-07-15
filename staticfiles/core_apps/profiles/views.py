from typing import List
from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from django.http import Http404
from django.contrib.auth import get_user_model
from rest_framework import filters, generics
from rest_framework.pagination import PageNumberPagination
from core_apps.common.renderers import GenericJsonRenderer
from .models import Profile
from .serializers import ProfileSerializer, UpdateProfileSerializer

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = "page_size"
    max_page_size = 100


class ProfileListAPIView(generics.ListAPIView):
    serializer_class = ProfileSerializer
    renderer_classes = [GenericJsonRenderer]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["user__first_name", "user__last_name"]
    filterset_fields = ["gender"]
    object_label = "profiles"

    def get_queryset(self) -> List[Profile]:
        return Profile.objects.exclude(user__is_staff=True).exclude(
            user__is_superuser=True
        )


class ProfileDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    renderer_classes = [GenericJsonRenderer]
    object_label = "Profile"

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
    object_label = "profile"

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
