"""Durable per-device retries. Provider acceptance is not device delivery proof."""

import logging
from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from ..models import DeviceToken, PushDelivery
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
    if not FCMService.should_send_to_user(
        user, notification.notification_type, scope=notification.scope
    ):
        return False
    data = notification.data or {}
    if notification.category == "account_policy" and data.get("case_id"):
        from django.core.exceptions import ValidationError as DjangoValidationError
        from core_apps.chat.models import ChatModerationCase

        try:
            if not ChatModerationCase.objects.filter(
                id=data["case_id"],
                notification=notification,
                subject=user,
                conversation__id=data.get("conversation_id"),
                resolved_at__isnull=True,
                state__in=["warning", "pending_review", "permanent"],
            ).exists():
                return False
        except (DjangoValidationError, ValueError, TypeError):
            return False
    planning_event = None
    if data.get("event_id") or data.get("event_source") == "planning":
        from django.core.exceptions import ValidationError as DjangoValidationError
        from django.http import Http404
        from rest_framework.exceptions import APIException
        from core_apps.features.planning_models import PlanningEvent
        from core_apps.features.services.planning_notifications_parts.event_copy import (
            event_copy,
        )

        try:
            # Chat, security and campaign events also use event_id. The persisted
            # relation identifies a planning receipt, never the field name alone.
            planning_event = (
                PlanningEvent.objects.select_related("recipient")
                .filter(recipient=user, notification=notification)
                .first()
            )
            if planning_event is None:
                if data.get("event_source") == "planning":
                    return False
            else:
                if not isinstance(planning_event.destination, dict):
                    return False
                if str(planning_event.id) != data.get("event_id"):
                    return False
                from .inbox_scope import canonical_scope

                if (
                    canonical_scope(
                        planning_event.destination, notification.notification_type
                    )
                    != notification.scope
                ):
                    return False
                if any(
                    data.get(key) != value
                    for key, value in planning_event.destination.items()
                    if key not in {"scope", "workspace", "presentation_workspace"}
                ):
                    return False
                event_copy(planning_event)
        except (
            APIException,
            Http404,
            DjangoValidationError,
            ValueError,
            TypeError,
            KeyError,
        ):
            return False
    if planning_event is None and data.get("event_kind") == "purchase_fulfilled":
        from django.core.exceptions import ValidationError as DjangoValidationError
        from django.http import Http404
        from rest_framework.exceptions import APIException
        from core_apps.features.services.billing_notifications import authorize

        try:
            authorize(user, data)
        except (APIException, Http404, DjangoValidationError, ValueError, TypeError):
            return False
    if planning_event is None and data.get("event_kind") in {
        "student_plan_changed",
        "student_arrangement_changed",
    }:
        from django.core.exceptions import ValidationError as DjangoValidationError
        from django.http import Http404
        from rest_framework.exceptions import APIException
        from core_apps.features.services.student_housing.notifications import authorize

        try:
            authorize(user, data)
        except (APIException, Http404, DjangoValidationError, ValueError, TypeError):
            return False
    if data.get("action_type") == "open_tenancy_invitation":
        from core_apps.features.services.tenancy_invitations_parts.notify_after_commit import (
            notice_allowed,
        )

        if not notice_allowed(notification):
            return False
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
        from core_apps.chat.services.inbox_preferences import notifications_muted

        if notifications_muted(participant):
            return False
        if chat.kind != "direct" or data.get("message_id"):
            from core_apps.chat.models import Message
            from core_apps.chat.services.group_notification_preferences import (
                allows_message,
            )

            try:
                message = Message.objects.get(
                    id=UUID(str(data.get("message_id"))), conversation=chat
                )
            except (ValueError, TypeError, Message.DoesNotExist):
                return False
            if not allows_message(participant, message):
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
        from .inbox_scope import receipt_data

        try:
            success = FCMService.send_push_to_device(
                token=item.device.token,
                title=notice.title,
                body=notice.body,
                data={**receipt_data(notice), "notification_id": str(notice.id)},
                language=item.device.language,
                device_type=item.device.device_type,
                chat_actions_version=item.device.chat_actions_version or 0,
            )
        except Exception:
            # Preserve this attempt for retry and let other deliveries progress.
            # Exception text can contain provider credentials or private content.
            logger.warning("Push attempt failed for delivery %s", item.pk)
            success = False
        PushDelivery.objects.filter(pk=identity).update(
            claimed_until=None,
            accepted_at=timezone.now() if success else None,
            next_attempt_at=timezone.now()
            + timedelta(seconds=min(30 * 2**item.attempts, 900)),
        )
        accepted += int(success)
        if success and notice.data.get("event_id"):
            from core_apps.features.planning_models import PlanningEvent

            PlanningEvent.objects.filter(
                notification=notice, provider_accepted_at__isnull=True
            ).update(
                provider_accepted_at=timezone.now(), delivery_status="provider_accepted"
            )
    return accepted
