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
            "action_type": "open_chat",
            "conversation_id": str(case.conversation.id),
            "case_id": str(case.id),
        },
        send_push=False,
    )
    case.notification = notification
    case.save(update_fields=["notification", "updated_at"])


def deliver_pending(limit=20):
    from core_apps.notifications.services.fcm_service import FCMService

    for pk in ChatModerationCase.objects.filter(
        notification__isnull=False,
        push_claimed_at__isnull=True,
        resolved_at__isnull=True,
    ).values_list("pk", flat=True)[:limit]:
        with transaction.atomic():
            case = (
                ChatModerationCase.objects.select_for_update()
                .select_related("notification", "subject")
                .get(pk=pk)
            )
            if case.push_claimed_at or case.resolved_at:
                continue
            case.push_claimed_at = timezone.now()
            case.save(update_fields=["push_claimed_at", "updated_at"])
        # At-most-once provider attempt. The durable in-app notice is authoritative
        # even if delivery is uncertain; never replay sensitive push payloads.
        n = case.notification
        try:
            FCMService.send_push_to_user(
                user=case.subject,
                title=n.title,
                body=n.body,
                data=n.data,
                notification_type="general",
            )
        except Exception:
            pass
