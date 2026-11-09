from rest_framework import serializers


class ParticipantSerializer(serializers.Serializer):
    """Read-only representation of a chat participant or message author."""

    id = serializers.UUIDField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    full_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()

    def get_full_name(self, user) -> str:
        return (
            user.get_full_name
            if hasattr(user, "get_full_name")
            else f"{user.first_name} {user.last_name}".strip()
        )

    def get_email(self, user) -> str:
        """A5-03: chat projections carry the approved public identity only.

        The key stays for client compatibility; it holds the address only when the
        participant is the requesting user. Counterparts always receive "".
        """
        request = self.context.get("request") if hasattr(self, "context") else None
        viewer = getattr(request, "user", None)
        if viewer is not None and getattr(viewer, "pk", None) == getattr(user, "pk", object()):
            return user.email or ""
        return ""

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
