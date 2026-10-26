"""Public, city-scoped maintained district choices."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, serializers
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.common.pagination import StandardResultsSetPagination
from ..models import City, District


class DistrictSerializer(serializers.ModelSerializer):
    city_id = serializers.UUIDField(source="city.id", read_only=True)

    def to_representation(self, instance):
        from ..catalog_labels import catalog_language, location_label

        result = super().to_representation(instance)
        result["name"] = location_label(instance, catalog_language(self.context))
        return result

    class Meta:
        model = District
        fields = ["id", "city_id", "name", "is_active", "revision", "sort_order"]


class DistrictListAPIView(generics.ListAPIView):
    serializer_class = DistrictSerializer
    renderer_classes = [GenericJsonRenderer]
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        city = get_object_or_404(City, id=self.kwargs["city_id"])
        return District.objects.filter(
            city=city,
            is_active=True,
            city__is_active=True,
            city__governorate__is_active=True,
        ).select_related("city")
