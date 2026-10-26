from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException
from core_apps.chat.models import ChatEvent, ChatNotificationDelivery
from .group_access import authorize, lock_conversation_root
from .group_events import event_payload
from .mentions import is_mentioned
from .group_notification_preferences import allows_message


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
    if not allows_message(participant, event.message):
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
                "workspace": "company",
            }
            if company
            else {
                "type": "housing_group_chat",
                "workspace": "student",
                "event_kind": "housing_group_chat",
                "group_id": group_id,
                "conversation_id": str(conversation.id),
                "message_id": str(event.message.id),
                "event_id": str(event.id),
                "deep_link": f"https://sokoun.app/housing-groups/{group_id}/chat?message_id={event.message.id}",
            }
        )
    )
    destination.update(
        {
            "chat_actions_version": "1",
            "recipient_id": str(user.id),
            "membership_period": str(participant.membership_period),
        }
    )
    if mentioned:
        destination["is_mention"] = "true"
    notification = NotificationService.create_notification(
        user=user,
        title=(
            "تمت الإشارة إليك في الشات"
            if mentioned
            else (
                "رسالة جديدة"
                if direct
                else (
                    "رسالة جديدة في مناقشة الشركة"
                    if company
                    else "رسالة جديدة في شات الجروب"
                )
            )
        ),
        body=(
            "افتح سكون لقراءة الرسالة التي تمت الإشارة إليك فيها"
            if mentioned
            else "افتح سكون لقراءة الرسالة"
        ),
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
    notification.data = {**notification.data, "notification_id": str(notification.id)}
    notification.save(update_fields=["data", "updated_at"])
    delivery.notification = notification
    delivery.save(update_fields=["notification", "updated_at"])


def deliver_pushes(limit=100, *, event_pk=None):
    """Atomically hand unclaimed notices to the durable per-device outbox."""
    from django.http import Http404
    from core_apps.notifications.services.push_delivery import queue_notification

    pending = ChatNotificationDelivery.objects.filter(
        push_claimed_at__isnull=True, notification__isnull=False
    )
    if event_pk is not None:
        pending = pending.filter(event_id=event_pk)
    ids = list(pending.values_list("pk", flat=True)[:limit])
    for identity in ids:
        initial = (
            ChatNotificationDelivery.objects.select_related("event__conversation")
            .filter(pk=identity)
            .first()
        )
        if initial is None:
            continue
        with transaction.atomic():
            lock_conversation_root(initial.event.conversation)
            delivery = (
                ChatNotificationDelivery.objects.select_for_update(of=("self",))
                .select_related(
                    "event__conversation", "event__message", "user", "notification"
                )
                .filter(pk=identity)
                .first()
            )
            if delivery is None or delivery.push_claimed_at:
                continue
            try:
                _, participant, _ = authorize(
                    delivery.event.conversation, delivery.user, lock=True
                )
                eligible = (
                    delivery.event.message is not None
                    and allows_message(participant, delivery.event.message)
                    and event_payload(delivery.event, delivery.user) is not None
                )
            except (APIException, Http404):
                eligible = False
            if eligible:
                # No provider I/O here. The device worker rechecks membership,
                # reads, deletions, mute, scope preference and session at each try.
                queue_notification(delivery.notification)
            delivery.push_claimed_at = timezone.now()
            delivery.save(update_fields=["push_claimed_at", "updated_at"])
