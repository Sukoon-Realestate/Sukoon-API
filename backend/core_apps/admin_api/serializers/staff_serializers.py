from rest_framework import serializers
from core_apps.admin_api.models import StaffProfile


class StaffProfileListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    roleName = serializers.SerializerMethodField()
    timeAgo = serializers.SerializerMethodField()
    avatarColor = serializers.SerializerMethodField()

    class Meta:
        model = StaffProfile
        fields = [
            "id",
            "name",
            "email",
            "role_name",
            "roleName",
            "display_role",
            "is_active",
            "timeAgo",
            "avatarColor",
        ]
        read_only_fields = fields

    def get_name(self, obj):
        return obj.user.get_full_name or obj.user.email

    def get_email(self, obj):
        return obj.user.email

    def get_roleName(self, obj):
        if obj.display_role:
            return obj.display_role
        return obj.get_role_name_display()

    def get_timeAgo(self, obj):
        return "مشرف نشط"

    def get_avatarColor(self, obj):
        color_map = {
            "system_owner": "bg-rose-100 text-rose-700 dark:bg-rose-500/20 dark:text-rose-400",
            "main_admin": "bg-teal-100 text-teal-700 dark:bg-teal-500/20 dark:text-teal-400",
            "kyc_reviewer": "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400",
            "property_reviewer": "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400",
            "support": "bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400",
        }
        return color_map.get(
            obj.role_name,
            "bg-teal-100 text-teal-700 dark:bg-teal-500/20 dark:text-teal-400",
        )


class StaffInviteSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    role_name = serializers.CharField(required=False, default="مراجع KYC")
