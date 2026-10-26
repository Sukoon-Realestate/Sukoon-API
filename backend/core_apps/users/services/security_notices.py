"""Account-scoped security history, durable mail attempts and existing push queue."""

from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from ..models import SecurityNotice


def deliver(limit=100):
    ids = (
        SecurityNotice.objects.filter(email_sent_at__isnull=True, attempts__lt=5)
        .order_by("created_at")
        .values_list("pk", flat=True)[:limit]
    )
    sent = 0
    for identity in ids:
        with transaction.atomic():
            item = (
                SecurityNotice.objects.select_for_update()
                .select_related("event__user")
                .get(pk=identity)
            )
            if item.email_sent_at or item.attempts >= 5:
                continue
            event = item.event
            title = "تحديث أمان الحساب | Account security update"
            body = (
                "تم تحديث طلب عامل التحقق. راجع أمان الحساب لمعرفة الحالة الحالية.\n"
                "Your verification-factor request changed. Review account security for its current status."
            )
            if not item.notification_id:
                from core_apps.notifications.models import Notification
                from core_apps.notifications.services.push_delivery import (
                    queue_notification,
                )

                item.notification = Notification.objects.create(
                    user=event.user,
                    notification_type="security_alert",
                    title=title,
                    body=body,
                    category="security_alerts",
                    icon_type="shield",
                    data={
                        "scope": "account",
                        "action_type": "open_account_security",
                        "target_id": str(event.subject_id),
                        "event_id": str(event.id),
                    },
                )
                queue_notification(item.notification)
            item.attempts += 1
            # Record failed delivery without undoing the business command or in-app notice.
            try:
                accepted = send_mail(
                    title,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [item.email_to],
                    fail_silently=False,
                )
            except Exception:
                accepted = 0
            if accepted == 1:
                item.email_sent_at = timezone.now()
                sent += 1
            item.save()
    return sent
