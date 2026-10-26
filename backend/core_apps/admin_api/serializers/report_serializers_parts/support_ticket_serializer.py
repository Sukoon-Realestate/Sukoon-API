"""Report serializers: support ticket serializer."""

from rest_framework import serializers
from core_apps.admin_api.models import UserReport


class UserReportListSerializer(serializers.ModelSerializer):
    reportedUser = serializers.SerializerMethodField()
    reportedUserId = serializers.SerializerMethodField()
    userType = serializers.SerializerMethodField()
    reporter = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    automationLevelDisplay = serializers.SerializerMethodField()
    statusDisplay = serializers.SerializerMethodField()
    chatPolicyCaseId = serializers.SerializerMethodField()

    class Meta:
        model = UserReport
        fields = [
            "id",
            "reportedUser",
            "reportedUserId",
            "userType",
            "reason",
            "reason_type",
            "reporter",
            "date",
            "automation_level",
            "automationLevelDisplay",
            "status",
            "statusDisplay",
            "notes",
            "created_at",
            "chatPolicyCaseId",
        ]
        read_only_fields = fields

    def get_chatPolicyCaseId(self, obj):
        case = getattr(obj, "chat_case", None)
        return str(case.id) if case else None

    def get_reportedUser(self, obj):
        return obj.reported_user.get_full_name or obj.reported_user.email

    def get_reportedUserId(self, obj):
        return str(obj.reported_user.id)

    def get_userType(self, obj):
        return "مالك" if obj.reported_user.properties.exists() else "مستأجر"

    def get_reporter(self, obj):
        if not obj.reporter:
            return "النظام الآلي"
        return obj.reporter.get_full_name or obj.reporter.email

    def get_date(self, obj):
        return obj.created_at.strftime("%Y/%m/%d %H:%M")

    def get_automationLevelDisplay(self, obj):
        mapping = {
            "high": "عالي",
            "auto": "تلقائي",
            "low": "منخفض",
        }
        return mapping.get(obj.automation_level, "تلقائي")

    def get_statusDisplay(self, obj):
        mapping = {
            "active": "نشط",
            "suspended": "موقوف مؤقتاً",
            "banned": "محظور نهائياً",
            "dismissed": "تم التجاهل",
        }
        return mapping.get(obj.status, "نشط")


class UserReportActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=["suspend_user", "ban_user", "dismiss", "mark_active"],
        required=True,
    )
    notes = serializers.CharField(required=False, default="", allow_blank=True)


class SupportTicketSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        from core_apps.support.services.operations import projection
        return projection(instance, self.context["request"].user)
