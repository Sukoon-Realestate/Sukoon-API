from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import APIException
from core_apps.chat.models import Conversation
from .group_access import authorize, eligible_participants
from .group_projection import sender_payload
from .group_rate_limit import enforce_rate


def broadcast_typing(conversation, user, *, started):
    _, participant, _ = authorize(conversation, user, action="send_message")
    key = f"chat-typing:{conversation.id}:{participant.membership_period}"
    if started and not cache.add(key, True, timeout=2):
        return
    enforce_rate(user, "typing", maximum=60)
    if not started:
        cache.delete(key)
    layer = get_channel_layer()
    if not layer:
        return
    for recipient in eligible_participants(conversation).exclude(user=user):
        async_to_sync(layer.group_send)(
            f"chat_user_{recipient.user.id}",
            {
                "type": "chat.group_typing",
                "conversation_id": str(conversation.id),
                "actor_id": str(user.id),
                "membership_period": str(participant.membership_period),
                "started": started,
                "expires_at": (timezone.now() + timedelta(seconds=5)).isoformat(),
            },
        )


def typing_payload(event, user):
    conversation = Conversation.objects.get(id=event["conversation_id"])
    try:
        authorize(conversation, user)
    except APIException:
        return None
    actor = (
        eligible_participants(conversation)
        .filter(
            user__id=event["actor_id"], membership_period=event["membership_period"]
        )
        .select_related("user")
        .first()
    )
    if not actor or timezone.now().isoformat() > event["expires_at"]:
        return None
    return {
        "type": "typing.started" if event["started"] else "typing.stopped",
        "payload": {
            "conversation_id": str(conversation.id),
            "sender": sender_payload(actor.user),
            "expires_at": event["expires_at"],
        },
    }
