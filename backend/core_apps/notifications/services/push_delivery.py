"""Durable per-device retries. Provider acceptance is not device delivery proof."""

import logging
from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from ..models import DeviceToken, Notification, PushDelivery
from .fcm_service import FCMService

logger = logging.getLogger(__name__)


def queue_notification(notification):
    devices = DeviceToken.objects.filter(user=notification.user, is_active=True)
    PushDelivery.objects.bulk_create(
        [PushDelivery(notification=notification, device=device) for device in devices],
        ignore_conflicts=True,
    )
    # The five-second worker sees committed rows only. No broker/provider IO
    # runs on the request thread or inside the domain transaction.


def allowed(item):
    device, notification = item.device, item.notification
    user = notification.user
    if not user.is_active or not device.is_active or device.user_id != user.pk:
        return False
    session = device.auth_session
    if session is None:
        if user.security_epoch or user.requires_bound_session:
            return False
    elif (
        session.user_id != user.pk
        or session.revoked_at
        or session.expires_at <= timezone.now()
        or session.security_epoch != user.security_epoch
    ):
        return False
    if not FCMService.should_send_to_user(user, notification.notification_type):
        return False
    data = notification.data or {}
    conversation = data.get("conversation_id") or data.get("chat_id")
    if conversation and notification.notification_type == "new_message":
        from uuid import UUID
        from django.http import Http404
        from rest_framework.exceptions import APIException
        from core_apps.chat.models import (
            Conversation,
            ConversationParticipant,
            ChatBlock,
        )
        from core_apps.chat.services.group_access import authorize

        try:
            identity = UUID(str(conversation))
            chat = Conversation.objects.get(id=identity)
            _, participant, _ = authorize(chat, user)
        except (
            ValueError,
            TypeError,
            Conversation.DoesNotExist,
            APIException,
            Http404,
        ):
            return False
        if participant.is_muted:
            return False
        peers = (
            ConversationParticipant.objects.filter(conversation__id=conversation)
            .exclude(user=user)
            .values_list("user_id", flat=True)
        )
        if ChatBlock.objects.filter(
            Q(user=user, blocked_user_id__in=peers)
            | Q(blocked_user=user, user_id__in=peers)
        ).exists():
            return False
    return True


def dispatch(limit=100):
    now = timezone.now()
    ids = list(
        PushDelivery.objects.filter(
            accepted_at__isnull=True,
            suppressed=False,
            attempts__lt=5,
            next_attempt_at__lte=now,
        )
        .filter(Q(claimed_until__isnull=True) | Q(claimed_until__lte=now))
        .order_by("next_attempt_at")
        .values_list("pk", flat=True)[:limit]
    )
    accepted = 0
    for identity in ids:
        with transaction.atomic():
            item = PushDelivery.objects.select_for_update().get(pk=identity)
            if (
                item.accepted_at
                or item.suppressed
                or item.attempts >= 5
                or item.next_attempt_at > timezone.now()
                or item.claimed_until
                and item.claimed_until > timezone.now()
            ):
                continue
            item.claimed_until = timezone.now() + timedelta(minutes=2)
            item.attempts += 1
            item.save(update_fields=["claimed_until", "attempts"])
        item = PushDelivery.objects.select_related(
            "device__auth_session", "notification__user"
        ).get(pk=identity)
        if not allowed(item):
            PushDelivery.objects.filter(pk=identity).update(
                suppressed=True, claimed_until=None
            )
            continue
        notice = item.notification
        success = FCMService.send_push_to_device(
            token=item.device.token,
            title=notice.title,
            body=notice.body,
            data={**(notice.data or {}), "notification_id": str(notice.id)},
            language=item.device.language,
        )
        PushDelivery.objects.filter(pk=identity).update(
            claimed_until=None,
            accepted_at=timezone.now() if success else None,
            next_attempt_at=timezone.now()
            + timedelta(seconds=min(30 * 2**item.attempts, 900)),
        )
        accepted += int(success)
    return accepted
