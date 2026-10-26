"""Durable private notices; no message/unread counter is synthesized."""

from django.db import transaction
from django.utils import timezone
from core_apps.chat.models import ChatModerationCase


def create_notice(case):
    from core_apps.notifications.services.notification_service import (
        NotificationService,
    )

    if case.notification_id or case.state not in {
        "warning",
        "pending_review",
        "permanent",
    }:
        return
    notification = NotificationService.create_notification(
        user=case.subject,
        title="تنبيه حماية التعاملات في سكون",
        body="يوجد تحديث بشأن الالتزام بسياسة التعاملات. افتح سكون لمراجعته.",
        notification_type="general",
        category="account_policy",
        icon_type="warning",
        data={
            "event_kind": "chat_policy_update",
            "scope": "account",
            "action_type": "open_chat",
            "conversation_id": str(case.conversation.id),
            "case_id": str(case.id),
        },
        send_push=False,
    )
    case.notification = notification
    case.save(update_fields=["notification", "updated_at"])


def deliver_pending(limit=20):
    from core_apps.notifications.services.push_delivery import queue_notification

    for pk in ChatModerationCase.objects.filter(
        notification__isnull=False,
        push_claimed_at__isnull=True,
        resolved_at__isnull=True,
    ).values_list("pk", flat=True)[:limit]:
        with transaction.atomic():
            case = (
                ChatModerationCase.objects.select_for_update(of=("self",))
                .select_related("notification", "subject")
                .get(pk=pk)
            )
            if case.push_claimed_at or case.resolved_at:
                continue
            queue_notification(case.notification)
            case.push_claimed_at = timezone.now()
            case.save(update_fields=["push_claimed_at", "updated_at"])
