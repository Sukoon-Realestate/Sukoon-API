"""Report serializers: overview ticket serializer."""

from rest_framework import serializers
from core_apps.admin_api.models import UserReport


class OverviewTicketSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    rawId = serializers.SerializerMethodField()
    subject = serializers.CharField(source="reason", read_only=True)
    reporter = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    reviewer = serializers.SerializerMethodField()

    class Meta:
        model = UserReport
        fields = [
            "id",
            "rawId",
            "subject",
            "reporter",
            "type",
            "status",
            "reviewer",
            "created_at",
        ]
        read_only_fields = fields

    def get_id(self, obj):
        return f"TKT-{str(obj.id)[:6].upper()}"

    def get_rawId(self, obj):
        return str(obj.id)

    def get_reporter(self, obj):
        if not obj.reporter:
            return "النظام الآلي"
        return obj.reporter.get_full_name or obj.reporter.email

    def get_type(self, obj):
        mapping = {
            "fraud": "خلاف",
            "misleading": "بلاغ عقار",
            "spam": "بلاغ مستخدم",
            "abusive": "خلاف",
            "other": "بلاغ مستخدم",
        }
        return mapping.get(obj.reason_type, "خلاف")

    def get_status(self, obj):
        mapping = {
            "active": "مفتوح",
            "suspended": "قيد المراجعة",
            "dismissed": "محلول",
            "banned": "مغلق",
        }
        return mapping.get(obj.status, "مفتوح")

    def get_reviewer(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name or obj.reviewed_by.email
        return "لم يُحدد"
