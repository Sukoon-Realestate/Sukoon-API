"""Private bookmarks, shared pins and honest per-message reading times."""

from datetime import timedelta
import hashlib
import json
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.chat.models import ChatEvent, MessageStar, MessagePin, MessageReadReceipt
from .group_access import authorize, visible_messages, eligible_participants, actions
from .group_limits import ChatConflict


class MessageToolBody(serializers.Serializer):
    membership_period = serializers.UUIDField()
    operation_id = serializers.UUIDField()
    enabled = serializers.BooleanField()
    duration_hours = serializers.ChoiceField(choices=[24, 168, 720], default=168)


def visible_message(conversation, participant, identity):
    return get_object_or_404(
        visible_messages(conversation, participant).exclude(kind="system"), id=identity, deleted_at__isnull=True
    )


def can_pin(conversation, participant, member):
    if "send_message" not in actions(member):
        return False
    if conversation.kind == "direct":
        return True
    if conversation.kind == "company_request":
        return conversation.company_request.coordinator_id == participant.user_id
    return member.role == "admin"


def star_payload(message, participant):
    star = next(
        (
            s
            for s in message.stars.all()
            if s.user_id == participant.user_id and s.membership_period == participant.membership_period
        ),
        None,
    )
    return {
        "is_starred": bool(star and star.enabled and not message.deleted_at),
        "star_revision": star.revision if star else 0,
    }


def pins_payload(conversation, participant, member):
    from .group_projection import message_payload

    pins = (
        MessagePin.objects.filter(
            message__conversation=conversation,
            message__sequence__gte=participant.visible_from_sequence,
            message__deleted_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .select_related("message__sender", "pinned_by")
        .order_by("-created_at")[:3]
    )
    return [
        {
            "message": message_payload(p.message, participant, member),
            "expires_at": p.expires_at.isoformat(),
            "pinned_by": str(p.pinned_by.id),
        }
        for p in pins
    ]


@transaction.atomic
def set_message_tool(conversation, user, identity, data, *, pin=False):
    from .group_events import record_event
    from .group_projection import message_payload, summary

    body = MessageToolBody(data=data)
    body.is_valid(raise_exception=True)
    values = body.validated_data
    conversation, participant, member = authorize(
        conversation, user, action="send_message" if pin else "read_chat", lock=True
    )
    if values["membership_period"] != participant.membership_period:
        raise ChatConflict("Refresh the current chat membership before retrying.")
    message = visible_message(conversation, participant, identity)
    if pin and not can_pin(conversation, participant, member):
        raise PermissionDenied("Only group administrators can pin messages.")
    fingerprint = hashlib.sha256(
        json.dumps([str(identity), "pin" if pin else "star", values], default=str, sort_keys=True).encode()
    ).hexdigest()
    receipt = ChatEvent.objects.filter(
        conversation=conversation, actor=user, data__operation_id=str(values["operation_id"])
    ).first()
    if receipt and receipt.data.get("fingerprint") != fingerprint:
        raise ChatConflict()
    if not receipt:
        if pin:
            MessagePin.objects.filter(message__conversation=conversation, expires_at__lte=timezone.now()).delete()
            if values["enabled"]:
                active = MessagePin.objects.filter(
                    message__conversation=conversation, message__deleted_at__isnull=True
                ).exclude(message=message)
                if active.count() >= 3:
                    raise ValidationError("Unpin a message before pinning another one.")
                MessagePin.objects.update_or_create(
                    message=message,
                    defaults={
                        "pinned_by": user,
                        "expires_at": timezone.now() + timedelta(hours=values["duration_hours"]),
                    },
                )
            else:
                MessagePin.objects.filter(message=message).delete()
        else:
            star, created = MessageStar.objects.get_or_create(
                message=message,
                user=user,
                membership_period=participant.membership_period,
                defaults={"enabled": values["enabled"]},
            )
            if not created:
                star.enabled = values["enabled"]
                star.revision += 1
                star.save(update_fields=["enabled", "revision", "updated_at"])
        record_event(
            conversation,
            "conversation.updated" if pin else "message.star",
            message=None if pin else message,
            actor=user,
            data={
                "operation_id": str(values["operation_id"]),
                "fingerprint": fingerprint,
                "user_id": str(user.id),
                "membership_period": str(participant.membership_period),
            },
        )
    message.refresh_from_db()
    return summary(conversation, user) if pin else message_payload(message, participant, member)


def record_reads(conversation, participant, through, read_at):
    rows = (
        visible_messages(conversation, participant)
        .filter(sequence__gt=participant.last_read_sequence, sequence__lte=through, deleted_at__isnull=True)
        .exclude(sender_id=participant.user_id)
        .exclude(kind="system")
    )
    MessageReadReceipt.objects.bulk_create(
        [
            MessageReadReceipt(
                message_id=pk,
                user_id=participant.user_id,
                membership_period=participant.membership_period,
                read_at=read_at,
            )
            for pk in rows.values_list("pk", flat=True)
        ],
        batch_size=500,
        ignore_conflicts=True,
    )


def message_readers(conversation, user, identity):
    conversation, participant, _ = authorize(conversation, user)
    message = visible_message(conversation, participant, identity)
    if message.sender_id != user.pk:
        raise PermissionDenied("Only the sender can view message reading details.")
    return message, eligible_participants(conversation).filter(visible_from_sequence__lte=message.sequence).exclude(
        user=user
    ).select_related("user").order_by("pk")


def reader_payload(message, reader):
    from .group_projection import sender_payload

    receipt = message.read_receipts.filter(user_id=reader.user_id, membership_period=reader.membership_period).first()
    return {
        "user": sender_payload(reader.user),
        "is_read": reader.last_read_sequence >= message.sequence,
        "read_at": receipt.read_at.isoformat() if receipt else None,
    }
