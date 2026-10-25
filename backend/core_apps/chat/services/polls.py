import hashlib
import json
import uuid
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.chat.models import MessagePoll, MessagePollVote, ChatEvent
from .group_access import authorize, eligible_participants
from .group_limits import ChatConflict
from .message_tools import visible_message


class PollDefinition(serializers.Serializer):
    question = serializers.CharField(max_length=200)
    options = serializers.ListField(child=serializers.CharField(max_length=80), min_length=2, max_length=10)
    allow_multiple = serializers.BooleanField(default=False)

    def validate_options(self, value):
        if len({label.casefold() for label in value}) != len(value):
            raise serializers.ValidationError("Poll options must be different.")
        return value


def normalize_poll(value):
    body = PollDefinition(data=value)
    body.is_valid(raise_exception=True)
    return dict(body.validated_data)


def create_poll(message, definition):
    MessagePoll.objects.create(
        message=message,
        question=definition["question"],
        allow_multiple=definition["allow_multiple"],
        options=[
            {"id": str(uuid.uuid5(message.id, str(i))), "text": text} for i, text in enumerate(definition["options"])
        ],
    )


def poll_payload(message, participant):
    if message.deleted_at or message.kind != "poll":
        return None
    poll = message.poll
    periods = dict(
        eligible_participants(message.conversation)
        .filter(visible_from_sequence__lte=message.sequence)
        .values_list("user_id", "membership_period")
    )
    votes = [v for v in poll.votes.all() if periods.get(v.user_id) == v.membership_period]
    mine = next((v.option_ids for v in votes if v.user_id == participant.user_id), [])
    return {
        "question": poll.question,
        "allow_multiple": poll.allow_multiple,
        "revision": poll.revision,
        "is_closed": poll.closed_at is not None,
        "voter_count": sum(bool(v.option_ids) for v in votes),
        "options": [
            {**o, "votes": sum(o["id"] in v.option_ids for v in votes), "is_mine": o["id"] in mine}
            for o in poll.options
        ],
    }


class PollCommand(serializers.Serializer):
    membership_period = serializers.UUIDField()
    operation_id = serializers.UUIDField()
    option_ids = serializers.ListField(child=serializers.UUIDField(), max_length=10, default=list)


@transaction.atomic
def change_poll(conversation, user, message_id, data, *, close=False):
    from .group_events import record_event
    from .group_projection import message_payload

    body = PollCommand(data=data)
    body.is_valid(raise_exception=True)
    values = body.validated_data
    conversation, participant, member = authorize(conversation, user, action="send_message", lock=True)
    if conversation.kind == "direct":
        raise ValidationError("Polls are available in group chats only.")
    if values["membership_period"] != participant.membership_period:
        raise ChatConflict("Refresh the current chat membership before retrying.")
    message = visible_message(conversation, participant, message_id)
    if message.kind != "poll":
        raise ValidationError("This message is not a poll.")
    poll = message.poll
    if close and message.sender_id != user.pk and member.role != "admin":
        raise PermissionDenied("Only the poll creator or group administrator can close it.")
    ids = sorted(str(v) for v in values["option_ids"])
    fingerprint = hashlib.sha256(
        json.dumps([str(message.id), close, ids, str(participant.membership_period)]).encode()
    ).hexdigest()
    receipt = ChatEvent.objects.filter(
        conversation=conversation, actor=user, data__operation_id=str(values["operation_id"])
    ).first()
    if receipt:
        if receipt.data.get("fingerprint") != fingerprint:
            raise ChatConflict()
        return message_payload(message, participant, member)
    if close:
        poll.closed_at = poll.closed_at or timezone.now()
    else:
        if poll.closed_at:
            raise ValidationError("This poll is closed.")
        if (
            len(ids) != len(set(ids))
            or not set(ids).issubset({o["id"] for o in poll.options})
            or (not poll.allow_multiple and len(ids) > 1)
        ):
            raise ValidationError("Choose valid poll options.")
        MessagePollVote.objects.update_or_create(
            poll=poll, user=user, defaults={"membership_period": participant.membership_period, "option_ids": ids}
        )
    poll.revision += 1
    poll.save(update_fields=["closed_at", "revision", "updated_at"])
    poll.refresh_from_db()
    record_event(
        conversation,
        "message.poll",
        message=message,
        actor=user,
        data={"operation_id": str(values["operation_id"]), "fingerprint": fingerprint},
    )
    return message_payload(message, participant, member)
