"""Connection-scoped renewable presence. Expired/abandoned leases are never online."""

from datetime import timedelta
from django.utils import timezone
from core_apps.chat.models import ChatPresenceLease

ONLINE_TTL_SECONDS = 300
ONLINE_KEY_PREFIX = "chat:user:online:"  # compatibility export


def set_user_online_status(user_id, is_online, connection_id="legacy"):
    # Keep the historical two-argument service usable without affecting sockets.
    identity = f"{user_id}:{connection_id}"
    if is_online:
        now = timezone.now()
        ChatPresenceLease.objects.filter(user_id=user_id, expires_at__lte=now).delete()
        ChatPresenceLease.objects.update_or_create(
            connection_id=identity,
            defaults={
                "user_id": user_id,
                "expires_at": now + timedelta(seconds=ONLINE_TTL_SECONDS),
            },
        )
    else:
        ChatPresenceLease.objects.filter(connection_id=identity, user_id=user_id).delete()


def is_user_online(user_id):
    return ChatPresenceLease.objects.filter(user_id=user_id, expires_at__gt=timezone.now()).exists()
