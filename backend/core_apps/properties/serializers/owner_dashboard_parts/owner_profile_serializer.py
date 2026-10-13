"""Owner dashboard: owner profile serializer."""

from rest_framework import serializers
from .owner_dashboard_pending_visit_serializer import (
    OwnerProfileHeaderSerializer,
    OwnerProfileStatsSerializer,
    OwnerProfileAccountDetailsSerializer,
    OwnerPrivacyNoticeSerializer,
)


class OwnerRecentReviewSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    reviewer_name = serializers.CharField(read_only=True)
    rating = serializers.IntegerField(read_only=True)
    comment = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class OwnerProfileSerializer(serializers.Serializer):
    """
    Serializer for Owner Profile screen ('ملفي الشخصي').
    """

    owner = OwnerProfileHeaderSerializer(read_only=True)
    stats = OwnerProfileStatsSerializer(read_only=True)
    account_details = OwnerProfileAccountDetailsSerializer(read_only=True)
    privacy_notice = OwnerPrivacyNoticeSerializer(read_only=True)
    recent_reviews = OwnerRecentReviewSerializer(many=True, read_only=True)
