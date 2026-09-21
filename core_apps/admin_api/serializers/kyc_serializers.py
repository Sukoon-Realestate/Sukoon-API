from rest_framework import serializers
from django.utils import timezone
from core_apps.admin_api.models import KYCSubmission


class KYCSubmissionListSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    userId = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    nationalIdMask = serializers.SerializerMethodField()
    waitTime = serializers.SerializerMethodField()
    hasWarning = serializers.SerializerMethodField()
    statusDisplay = serializers.SerializerMethodField()

    class Meta:
        model = KYCSubmission
        fields = [
            "id",
            "user",
            "userId",
            "type",
            "nationalIdMask",
            "waitTime",
            "status",
            "statusDisplay",
            "hasWarning",
            "created_at",
        ]
        read_only_fields = fields

    def get_user(self, obj):
        return obj.profile.user.get_full_name or obj.profile.user.email

    def get_userId(self, obj):
        return str(obj.profile.user.id)

    def get_type(self, obj):
        return "مالك" if obj.profile.user.properties.exists() else "مستأجر"

    def get_nationalIdMask(self, obj):
        nid = obj.profile.national_id
        if not nid or len(nid) < 6:
            return "298•••••12"
        return f"{nid[:3]}•••••{nid[-2:]}"

    def get_waitTime(self, obj):
        delta = timezone.now() - obj.created_at
        if delta.days > 0:
            return f"{delta.days} أيام"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours} ساعات"
        mins = delta.seconds // 60
        return f"{mins} دقيقة"

    def get_hasWarning(self, obj):
        return obj.profile.user.reports_received.filter(status="active").exists()

    def get_statusDisplay(self, obj):
        if obj.status == KYCSubmission.Status.PENDING:
            return "انتظار المراجعة"
        elif obj.status == KYCSubmission.Status.APPROVED:
            return "مقبول"
        return "مرفوض"


class KYCRejectActionSerializer(serializers.Serializer):
    reason = serializers.CharField(
        required=True,
        error_messages={"required": "يرجى كتابة سبب رفض التوثيق."},
    )
