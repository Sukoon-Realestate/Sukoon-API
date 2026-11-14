"""Authenticated OS actions target the delivered message, never the latest message."""

from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from core_apps.chat.models import ChatNotificationDelivery
from core_apps.chat.services.group_access import authorize, visible_messages
from core_apps.chat.services.group_operations import mark_group_read
from core_apps.chat.services.group_send import send_group_message
from core_apps.chat.services.group_rate_limit import enforce_rate


@transaction.atomic
def apply_notification_action(user, values):
    if values["recipient_id"] != user.id:
        raise PermissionDenied("This notification belongs to another account.")
    delivery = get_object_or_404(
        ChatNotificationDelivery.objects.select_related(
            "event__conversation", "event__message", "notification"
        ),
        notification__id=values["notification_id"],
        user=user,
    )
    conversation, participant, _ = authorize(
        delivery.event.conversation,
        user,
        action="send_message" if values["action"] == "reply" else "mark_read",
        lock=True,
    )
    if str(participant.membership_period) != str(values["membership_period"]) or str(
        participant.membership_period
    ) != delivery.notification.data.get("membership_period"):
        raise PermissionDenied(
            "This notification belongs to an earlier chat membership."
        )
    notified = get_object_or_404(
        visible_messages(conversation, participant), pk=delivery.event.message_id
    )
    enforce_rate(user, "preferences" if values["action"] == "mark_read" else "send")
    message = None
    if values["action"] == "reply":
        message = send_group_message(
            conversation,
            user,
            {
                "client_message_id": str(values["client_message_id"]),
                "kind": "text",
                "content": values.get("content", ""),
                "membership_period": str(values["membership_period"]),
            },
        )
    read = mark_group_read(conversation, user, notified.sequence)
    delivery.notification.is_read = True
    delivery.notification.read_at = delivery.notification.read_at or timezone.now()
    delivery.notification.save(update_fields=["is_read", "read_at", "updated_at"])
    return {
        "conversation_id": str(conversation.id),
        "message_id": str(message.id) if message else None,
        "last_read_sequence": read["last_read_sequence"],
        "action": values["action"],
    }
