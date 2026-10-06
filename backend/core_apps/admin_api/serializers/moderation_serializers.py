from rest_framework import serializers
from core_apps.properties.models import Property


class ModerationItemSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    rawId = serializers.SerializerMethodField()
    property_id = serializers.SerializerMethodField()
    reason = serializers.SerializerMethodField()
    riskLevel = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "rawId",
            "property_id",
            "title",
            "reason",
            "riskLevel",
            "type",
            "created_at",
        ]
        read_only_fields = fields

    def get_id(self, obj):
        return f"mod-{str(obj.id)[:6]}"

    def get_rawId(self, obj):
        return str(obj.id)

    def get_property_id(self, obj):
        return str(obj.id)

    def get_reason(self, obj):
        owner_name = obj.owner.get_full_name or obj.owner.email
        if obj.status == Property.Status.NEEDS_REVISION:
            return f"وصف غير دقيق – يحتاج مراجعة • {owner_name}"
        if not obj.main_image:
            return f"صورة مفقودة أو غير واضحة • {owner_name}"
        return f"مراجعة محتوى وصور جديدة • {owner_name}"

    def get_riskLevel(self, obj):
        if obj.status == Property.Status.NEEDS_REVISION:
            return "متوسط"
        if not obj.is_verified:
            return "عالي"
        return "منخفض"

    def get_type(self, obj):
        # ? Returns 'صور' or 'نصوص'
        if not obj.main_image or obj.status == Property.Status.UNDER_REVIEW:
            return "صور"
        return "نصوص"


class ModerationMetricsSerializer(serializers.Serializer):
    suspiciousImages = serializers.IntegerField()
    misleadingDesc = serializers.IntegerField()
    phoneNumInPhotos = serializers.IntegerField()
    inappropriateContent = serializers.IntegerField()
