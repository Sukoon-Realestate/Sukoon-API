from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class AdminUserListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    kycStatus = serializers.SerializerMethodField()
    regDate = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    visitRequests = serializers.SerializerMethodField()
    reportsAgainst = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "first_name",
            "last_name",
            "email",
            "type",
            "status",
            "kycStatus",
            "regDate",
            "phone",
            "visitRequests",
            "reportsAgainst",
            "is_active",
            "is_verified",
        ]
        read_only_fields = fields

    def get_name(self, obj):
        return obj.get_full_name or obj.email

    def get_type(self, obj):
        # If annotated properties_count exists, use it; else fallback
        props_count = getattr(obj, "properties_count", None)
        if props_count is not None:
            return "مالك" if props_count > 0 else "مستأجر"
        return "مالك" if obj.properties.exists() else "مستأجر"

    def get_status(self, obj):
        if not obj.is_active:
            return "موقوف"
        return "نشط" if obj.is_verified else "قيد المراجعة"

    def get_kycStatus(self, obj):
        if obj.is_verified:
            return "موثق"
        profile = getattr(obj, "profile", None)
        if profile and hasattr(profile, "kyc_submissions"):
            first_sub = profile.kyc_submissions.first()
            if first_sub:
                if first_sub.status == "approved":
                    return "موثق"
                elif first_sub.status == "rejected":
                    return "مرفوض"
                return "قيد المراجعة"
        return "قيد المراجعة"

    def get_regDate(self, obj):
        return obj.date_joined.strftime("%Y/%m/%d") if obj.date_joined else ""

    def get_phone(self, obj):
        profile = getattr(obj, "profile", None)
        return str(profile.phone_number) if profile and profile.phone_number else ""

    def get_visitRequests(self, obj):
        count = getattr(obj, "visit_requests_count", None)
        if count is not None:
            return count
        return obj.visits.count() if hasattr(obj, "visits") else 0

    def get_reportsAgainst(self, obj):
        count = getattr(obj, "reports_count", None)
        if count is not None:
            return count
        return obj.reports_received.count() if hasattr(obj, "reports_received") else 0


class AdminUserSuspendSerializer(serializers.Serializer):
    reason = serializers.CharField(
        required=False, default="إيقاف إداري للحساب", allow_blank=True
    )
