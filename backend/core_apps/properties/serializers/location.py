from rest_framework import serializers

from ..models import City, Governorate


class PublicUUIDRelatedField(serializers.SlugRelatedField):
    """Use a related model's public UUID for both input and output."""

    def __init__(self, **kwargs):
        super().__init__(slug_field="id", **kwargs)

    def to_representation(self, obj):
        return str(super().to_representation(obj))


class GovernorateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Governorate
        fields = ["id", "name", "slug", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CitySerializer(serializers.ModelSerializer):
    governorate = PublicUUIDRelatedField(queryset=Governorate.objects.all())
    governorate_name = serializers.CharField(source="governorate.name", read_only=True)

    class Meta:
        model = City
        fields = [
            "id",
            "name",
            "slug",
            "governorate",
            "governorate_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "governorate_name", "created_at", "updated_at"]
