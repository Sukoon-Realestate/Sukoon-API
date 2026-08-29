import logging

import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from core_apps.common.renderers import GenericJsonRenderer

from ..models import City, Governorate
from ..serializers import CitySerializer, GovernorateSerializer

logger = logging.getLogger(__name__)


class CityFilter(django_filters.FilterSet):
    governorate = django_filters.UUIDFilter(field_name="governorate__id")

    class Meta:
        model = City
        fields = ["governorate"]


class GovernorateListAPIView(generics.ListAPIView):
    """List governorates, with optional name/slug search."""

    queryset = Governorate.objects.all()
    serializer_class = GovernorateSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "slug"]


class CityListAPIView(generics.ListAPIView):
    """List cities; filter with ``?governorate=<governorate UUID>``."""

    queryset = City.objects.select_related("governorate").all()
    serializer_class = CitySerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = CityFilter
    search_fields = ["name", "slug", "governorate__name"]
