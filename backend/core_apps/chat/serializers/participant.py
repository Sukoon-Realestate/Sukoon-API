from rest_framework import serializers


class ParticipantSerializer(serializers.Serializer):
    """Read-only representation of a chat participant or message author."""

    id = serializers.UUIDField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField()
    avatar_url = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()

    def get_full_name(self, user) -> str:
        return (
            user.get_full_name
            if hasattr(user, "get_full_name")
            else f"{user.first_name} {user.last_name}".strip()
        )

    def get_avatar_url(self, user) -> str:
        try:
            if hasattr(user, "profile") and user.profile.avatar:
                avatar = user.profile.avatar
                return avatar.url if hasattr(avatar, "url") else str(avatar)
        except Exception:
            pass
        return ""

    def get_is_online(self, user) -> bool:
        # ? Check online status cached in Redis or fallback to False
        try:
            from core_apps.chat.services.message_service import is_user_online

            return is_user_online(user_id=str(user.id))
        except Exception:
            return False
