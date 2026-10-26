from rest_framework import serializers

from ..models import City, Governorate
from ..catalog_labels import catalog_language, location_label


class PublicUUIDRelatedField(serializers.SlugRelatedField):
    """Use a related model's public UUID for both input and output."""

    def __init__(self, **kwargs):
        super().__init__(slug_field="id", **kwargs)

    def to_representation(self, obj):
        return str(super().to_representation(obj))


class GovernorateSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        result = super().to_representation(instance)
        result["name"] = location_label(instance, catalog_language(self.context))
        return result

    class Meta:
        model = Governorate
        fields = [
            "id",
            "name",
            "slug",
            "revision",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CitySerializer(serializers.ModelSerializer):
    governorate = PublicUUIDRelatedField(queryset=Governorate.objects.all())
    governorate_name = serializers.CharField(source="governorate.name", read_only=True)

    def to_representation(self, instance):
        result = super().to_representation(instance)
        language = catalog_language(self.context)
        result["name"] = location_label(instance, language)
        result["governorate_name"] = location_label(instance.governorate, language)
        return result

    class Meta:
        model = City
        fields = [
            "id",
            "name",
            "slug",
            "governorate",
            "governorate_name",
            "revision",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "governorate_name", "created_at", "updated_at"]
