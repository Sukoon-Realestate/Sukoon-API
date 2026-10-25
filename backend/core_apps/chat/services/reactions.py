"""One explicit reaction per account; retries never toggle a newer choice."""

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from core_apps.chat.models import ChatEvent, MessageReaction
from .group_access import authorize, visible_messages
from .group_events import record_event
from .group_limits import ChatConflict
from .group_projection import message_payload


@lru_cache(maxsize=1)
def emoji_catalog():
    source = Path(__file__).resolve().parent.parent / "data" / "emoji16.json"
    return {
        value.replace("\ufe0f", ""): value
        for value in json.loads(source.read_text())["emoji"]
    }


class ReactionInput(serializers.Serializer):
    emoji = serializers.CharField(max_length=64, allow_null=True, trim_whitespace=False)
    operation_id = serializers.UUIDField()
    membership_period = serializers.UUIDField()

    def validate_emoji(self, value):
        if value is None:
            return None
        canonical = emoji_catalog().get(value.replace("\ufe0f", ""))
        if canonical is None:
            raise serializers.ValidationError("Choose a single emoji.")
        return canonical


@transaction.atomic
def set_reaction(conversation, user, message_id, data):
    body = ReactionInput(data=data)
    body.is_valid(raise_exception=True)
    values = body.validated_data
    conversation, participant, member = authorize(
        conversation, user, action="send_message", lock=True
    )
    if values["membership_period"] != participant.membership_period:
        raise ChatConflict("Refresh the current chat membership before retrying.")
    message = get_object_or_404(
        visible_messages(conversation, participant), id=message_id
    )
    fingerprint = hashlib.sha256(
        json.dumps(
            [str(message.id), values["emoji"], str(participant.membership_period)],
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    operation_id = str(values["operation_id"])
    receipt = ChatEvent.objects.filter(
        conversation=conversation, actor=user, data__operation_id=operation_id
    ).first()
    if receipt:
        if receipt.data.get("fingerprint") != fingerprint:
            raise ChatConflict()
        return message_payload(message, participant, member)
    if message.deleted_at or message.kind == "system":
        raise serializers.ValidationError("This message is unavailable.")
    if values["emoji"] is None:
        MessageReaction.objects.filter(message=message, user=user).delete()
    else:
        MessageReaction.objects.update_or_create(
            message=message,
            user=user,
            defaults={
                "emoji": values["emoji"],
                "membership_period": participant.membership_period,
            },
        )
    message.reactions_revision += 1
    message.save(update_fields=["reactions_revision"])
    record_event(
        conversation,
        "message.reaction",
        message=message,
        actor=user,
        data={"operation_id": operation_id, "fingerprint": fingerprint},
    )
    return message_payload(message, participant, member)


def reaction_payload(message, participant):
    if message.deleted_at or message.kind == "system":
        return []
    grouped = {}
    for reaction in message.reactions.all():
        item = grouped.setdefault(
            reaction.emoji, {"emoji": reaction.emoji, "count": 0, "is_mine": False}
        )
        item["count"] += 1
        item["is_mine"] |= (
            reaction.user_id == participant.user_id
            and reaction.membership_period == participant.membership_period
        )
    return sorted(grouped.values(), key=lambda item: (-item["count"], item["emoji"]))
