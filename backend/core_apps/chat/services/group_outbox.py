from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException
from core_apps.chat.models import ChatEvent, ChatNotificationDelivery
from .group_access import authorize, lock_conversation_root
from .group_events import event_payload
from .mentions import is_mentioned


def drain_outbox(limit=100):
    delivered = 0
    for identity in (
        ChatEvent.objects.filter(delivered_at__isnull=True)
        .order_by("pkid")
        .values_list("pk", flat=True)[:limit]
    ):
        if deliver_event(identity):
            delivered += 1
    return delivered


def deliver_event(identity):
    # Lock order matches commands. Row locking serializes concurrent workers.
    initial = ChatEvent.objects.select_related("conversation").get(pk=identity)
    with transaction.atomic():
        lock_conversation_root(initial.conversation)
        event = (
            ChatEvent.objects.select_for_update(of=("self",))
            .select_related("conversation", "message", "actor")
            .get(pk=identity)
        )
        if event.delivered_at:
            return False
        event.attempts += 1
        channel = get_channel_layer()
        for participant in event.conversation.participant_set.select_related("user"):
            user = participant.user
            if event_payload(event, user) is None:
                continue
            if channel:
                # Consumers recheck access and serialize at delivery, never forward stale content.
                async_to_sync(channel.group_send)(
                    f"chat_user_{user.id}",
                    {"type": "chat.group_event", "event_id": str(event.id)},
                )
            _notify(event, user)
        event.delivered_at = timezone.now()
        event.save(update_fields=["delivered_at", "attempts", "updated_at"])
    return True


def _notify(event, user):
    if (
        event.kind != "message.new"
        or not event.message
        or event.message.kind == "system"
        or event.message.deleted_at
        or event.actor_id == user.pk
    ):
        return
    try:
        conversation, participant, _ = authorize(event.conversation, user)
    except APIException:
        return
    mentioned = is_mentioned(event.message, participant)
    if (participant.is_muted and not mentioned) or participant.last_read_sequence >= event.message.sequence:
        return
    delivery, _ = ChatNotificationDelivery.objects.get_or_create(event=event, user=user)
    if delivery.notification_id:
        return
    from core_apps.notifications.services.notification_service import (
        NotificationService,
    )

    company = conversation.kind == "company_request"
    direct = conversation.kind == "direct"
    group_id = "" if company or direct else str(conversation.housing_group.id)
    from .conversation_preferences import viewer_workspace
    destination = (
        {
            "type": "new_message",
            "conversation_id": str(conversation.id),
            "message_id": str(event.message.id),
            "sender_id": str(event.actor.id),
            "workspace": viewer_workspace(conversation, user),
        }
        if direct
        else (
            {
                "type": "company_request_chat",
                "action_type": "open_company_discussion",
                "target_id": str(conversation.company_request.id),
                "company_id": str(conversation.company_request.company.id),
                "conversation_id": str(conversation.id),
                "message_id": str(event.message.id),
                "schema_version": "1",
                "workspace": "tenant",
            }
            if company
            else {
                "type": "housing_group_chat",
                "event_kind": "housing_group_chat",
                "group_id": group_id,
                "conversation_id": str(conversation.id),
                "message_id": str(event.message.id),
                "event_id": str(event.id),
                "deep_link": f"https://sokoun.app/housing-groups/{group_id}/chat?message_id={event.message.id}",
            }
        )
    )
    if mentioned:
        destination["is_mention"] = "true"
    notification = NotificationService.create_notification(
        user=user,
        title=(
            "تمت الإشارة إليك في الشات" if mentioned else
            "رسالة جديدة"
            if direct
            else (
                "رسالة جديدة في مناقشة الشركة"
                if company
                else "رسالة جديدة في شات الجروب"
            )
        ),
        body="افتح سكون لقراءة الرسالة التي تمت الإشارة إليك فيها" if mentioned else "افتح سكون لقراءة الرسالة",
        notification_type="new_message",
        category=(
            "chat"
            if direct
            else "company_request_chat" if company else "housing_group_chat"
        ),
        icon_type="chat",
        data=destination,
        send_push=False,
    )
    delivery.notification = notification
    delivery.save(update_fields=["notification", "updated_at"])


def deliver_pushes(limit=100, *, event_pk=None):
    """Claim once before provider I/O. Provider exactly-once delivery is not assumed."""
    from core_apps.notifications.services.fcm_service import FCMService
    from contextlib import nullcontext

    pending = ChatNotificationDelivery.objects.filter(
        push_claimed_at__isnull=True, notification__isnull=False
    )
    if event_pk is not None:
        pending = pending.filter(event_id=event_pk)
    ids = pending.values_list("pk", flat=True)[:limit]
    for identity in ids:
        initial = ChatNotificationDelivery.objects.select_related(
            "event__conversation"
        ).get(pk=identity)
        with transaction.atomic():
            lock_conversation_root(initial.event.conversation)
            delivery = (
                ChatNotificationDelivery.objects.select_for_update(of=("self",))
                .select_related(
                    "event__conversation", "event__message", "user", "notification"
                )
                .get(pk=identity)
            )
            if delivery.push_claimed_at:
                continue
            delivery.push_claimed_at = timezone.now()
            delivery.save(update_fields=["push_claimed_at", "updated_at"])
        # Company delivery rechecks current case authority immediately before
        # dispatch, without retaining database locks during provider I/O.
        company = delivery.event.conversation.kind == "company_request"
        with nullcontext() if company else transaction.atomic():
            try:
                _, participant, _ = authorize(
                    delivery.event.conversation, delivery.user, lock=not company
                )
            except APIException:
                continue
            delivery.event.message.refresh_from_db()
            if (
                (participant.is_muted and not is_mentioned(delivery.event.message, participant))
                or participant.last_read_sequence >= delivery.event.message.sequence
                or event_payload(delivery.event, delivery.user) is None
                or delivery.event.message.deleted_at
            ):
                continue
            n = delivery.notification
            FCMService.send_push_to_user(
                user=delivery.user,
                title=n.title,
                body=n.body,
                data=n.data,
                notification_type="new_message",
            )
