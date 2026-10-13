"""Property: property statistics serializer."""

from rest_framework import serializers
from ...models import PropertyType


class AvailablePlacesQuerySerializer(serializers.Serializer):
    property_type_id = serializers.SlugRelatedField(
        slug_field="id", queryset=PropertyType.objects.all(), source="property_type"
    )


class DailyViewSerializer(serializers.Serializer):
    date = serializers.DateField()
    day = serializers.CharField()
    day_name = serializers.CharField()
    count = serializers.IntegerField()


class TopSearchCriterionSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    percentage = serializers.IntegerField()


class PropertyStatisticsSerializer(serializers.Serializer):
    """
    Detailed analytics for an owner's property listing matching the mobile screen:
    - 4 KPI cards: visit_requests_count, views_count, acceptance_rate, saved_count
    - Period selector (e.g. 30 days)
    - Views last 14 days chart (views_last_14_days)
    - Top search criteria breakdown (top_search_criteria)
    """

    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    period = serializers.CharField(read_only=True)
    period_label = serializers.CharField(read_only=True)

    # 4 Main KPI Cards
    visit_requests_count = serializers.IntegerField(read_only=True)
    views_count = serializers.IntegerField(read_only=True)
    acceptance_rate = serializers.IntegerField(read_only=True)
    saved_count = serializers.IntegerField(read_only=True)

    # 14-day views bar chart
    views_last_14_days = DailyViewSerializer(many=True, read_only=True)

    # Top search criteria breakdown
    top_search_criteria = TopSearchCriterionSerializer(many=True, read_only=True)

    # Extended metrics (backward-compatible)
    visits_count = serializers.IntegerField(read_only=True)
    recent_views_count = serializers.IntegerField(read_only=True)
    upcoming_visits_count = serializers.IntegerField(read_only=True)
    favorites_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    ratings_count = serializers.IntegerField(read_only=True)
    visits_summary = serializers.DictField(
        child=serializers.IntegerField(), read_only=True
    )


class PropertyVisibilitySerializer(serializers.Serializer):
    """
    Serializer to toggle or set property visibility (hidden/active).
    """

    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_hidden = serializers.BooleanField(required=False)
    message = serializers.CharField(read_only=True)
