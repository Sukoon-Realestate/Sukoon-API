"""One notification decision at creation and again immediately before delivery."""

from rest_framework.exceptions import ValidationError
from core_apps.chat.models import ConversationParticipant
from .inbox_preferences import notifications_muted
from .mentions import is_mentioned

Mode = ConversationParticipant.NotificationMode


def payload(conversation, participant):
    return {
        "supports_mention_notifications": conversation.kind != "direct",
        "notification_mode": (
            Mode.MUTED
            if notifications_muted(participant)
            else participant.notification_mode
        ),
        "notify_all_mentions": participant.notify_all_mentions,
    }


def apply(conversation, participant, data):
    if not {"notification_mode", "notify_all_mentions"}.intersection(data):
        return
    if conversation.kind == "direct":
        raise ValidationError(
            "Mention notification settings belong to group conversations."
        )
    if "notify_all_mentions" in data:
        if type(data["notify_all_mentions"]) is not bool:
            raise ValidationError({"notify_all_mentions": "Supply a boolean."})
        participant.notify_all_mentions = data["notify_all_mentions"]
    if "notification_mode" in data:
        mode = data["notification_mode"]
        if mode not in Mode.values or {"is_muted", "mute_duration"}.intersection(data):
            raise ValidationError(
                {"notification_mode": "Choose all messages, mentions only or mute."}
            )
        participant.is_muted = mode == Mode.MUTED
        participant.muted_until = None
        if mode != Mode.MUTED:
            participant.notification_mode = mode


def allows_message(participant, message):
    if (
        notifications_muted(participant)
        or message.deleted_at
        or message.kind == "system"
    ):
        return False
    if (
        message.sender_id == participant.user_id
        or message.sequence <= participant.last_read_sequence
    ):
        return False
    if message.sequence < participant.visible_from_sequence:
        return False
    if participant.conversation.kind == "direct":
        return True
    personal = any(
        item.get("kind") != "all"
        and item.get("user_id") == str(participant.user.id)
        and item.get("membership_period") == str(participant.membership_period)
        for item in message.mentions
    )
    broadcast = any(item.get("kind") == "all" for item in message.mentions)
    if personal:
        return True
    if broadcast:
        return participant.notify_all_mentions and is_mentioned(message, participant)
    return participant.notification_mode == Mode.ALL
