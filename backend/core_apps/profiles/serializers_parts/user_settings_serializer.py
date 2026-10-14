"""Serializers: user settings serializer."""

from rest_framework import serializers
from ..models import UserSettings


class UserSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for Screen: 'الإعدادات والخصوصية' (Settings and Privacy).
    Supports GET (view settings) and PUT/PATCH (save changes).
    """

    always_hide_mobile_number = serializers.BooleanField(
        read_only=True,
        default=True,
        help_text="Always hide mobile number for privacy protection (cannot be changed)",
    )
    always_hide_mobile_number_locked = serializers.SerializerMethodField(read_only=True)
    sections = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserSettings
        fields = [
            "id",
            # Notifications
            "visit_notifications",
            "new_properties_in_area",
            "owner_messages",
            "property_updates",
            "security_alerts",
            "promotions_and_updates",
            # Privacy
            "always_hide_mobile_number",
            "always_hide_mobile_number_locked",
            "share_location_for_search",
            "show_profile_in_search",
            # Grouped representation
            "sections",
        ]
        read_only_fields = [
            "id",
            "always_hide_mobile_number",
            "always_hide_mobile_number_locked",
            "sections",
        ]

    def get_always_hide_mobile_number_locked(self, obj: UserSettings) -> bool:
        return True

    def get_sections(self, obj: UserSettings) -> dict:
        return {
            "notifications": {
                "title": "الإشعارات",
                "items": [
                    {
                        "key": "visit_notifications",
                        "title": "طلبات الزيارات",
                        "subtitle": "قبول ورفض مواعيد الزيارة",
                        "value": obj.visit_notifications,
                        "enabled": True,
                    },
                    {
                        "key": "owner_messages",
                        "title": "الرسائل الجديدة",
                        "subtitle": "إشعار عند وصول رسالة",
                        "value": obj.owner_messages,
                        "enabled": True,
                    },
                    {
                        "key": "property_updates",
                        "title": "تحديثات العقارات",
                        "subtitle": "تغيير السعر أو الحالة",
                        "value": getattr(obj, "property_updates", False),
                        "enabled": True,
                    },
                    {
                        "key": "security_alerts",
                        "title": "التنبيهات الأمنية",
                        "subtitle": "دخول جديد وتغيير كلمة المرور",
                        "value": getattr(obj, "security_alerts", True),
                        "enabled": True,
                    },
                    {
                        "key": "promotions_and_updates",
                        "title": "العروض الترويجية",
                        "subtitle": "أخبار وعروض سكون",
                        "value": obj.promotions_and_updates,
                        "enabled": True,
                    },
                ],
                "footer_note": "يمكنك أيضاً إدارة إشعارات التطبيق من إعدادات هاتفك مباشرة.",
            },
            "privacy": {
                "title": "الخصوصية",
                "items": [
                    {
                        "key": "always_hide_mobile_number",
                        "title": "إخفاء رقم الموبايل دائماً",
                        "subtitle": "لا يمكن تغييره – لحماية خصوصيتك",
                        "value": obj.always_hide_mobile_number,
                        "enabled": False,
                        "locked": True,
                    },
                    {
                        "key": "share_location_for_search",
                        "title": "مشاركة موقعي للبحث",
                        "subtitle": "",
                        "value": obj.share_location_for_search,
                        "enabled": True,
                        "locked": False,
                    },
                    {
                        "key": "show_profile_in_search",
                        "title": "ظهور حسابي في البحث",
                        "subtitle": "",
                        "value": obj.show_profile_in_search,
                        "enabled": True,
                        "locked": False,
                    },
                ],
            },
        }

    def to_internal_value(self, data):
        # ? Support both flat and nested payloads ({ "notifications": {...}, "privacy": {...} })
        mutable_data = data.copy() if hasattr(data, "copy") else dict(data)
        if "notifications" in mutable_data and isinstance(
            mutable_data["notifications"], dict
        ):
            for k, v in mutable_data.pop("notifications").items():
                mutable_data.setdefault(k, v)
        if "privacy" in mutable_data and isinstance(mutable_data["privacy"], dict):
            for k, v in mutable_data.pop("privacy").items():
                mutable_data.setdefault(k, v)
        return super().to_internal_value(mutable_data)


class OwnerUnreadCountsSerializer(serializers.Serializer):
    """
    Serializer for Owner badge / unread counts:
    - visit_requests_count
    - unread_chat_messages_count
    - unread_notifications_count
    """

    visit_requests_count = serializers.IntegerField(read_only=True)
    unread_chat_messages_count = serializers.IntegerField(read_only=True)
    unread_notifications_count = serializers.IntegerField(read_only=True)


class TenantUnreadCountsSerializer(serializers.Serializer):
    """
    Serializer for Tenant badge / unread counts:
    - favorites_count
    - unread_chat_messages_count
    - unread_notifications_count
    - visit_requests_count
    """

    favorites_count = serializers.IntegerField(read_only=True)
    group_join_requests_count = serializers.IntegerField(read_only=True)
    unread_chat_messages_count = serializers.IntegerField(read_only=True)
    unread_notifications_count = serializers.IntegerField(read_only=True)
    visit_requests_count = serializers.IntegerField(read_only=True)
