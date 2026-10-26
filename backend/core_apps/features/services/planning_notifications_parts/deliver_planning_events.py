"""Planning notifications: deliver planning events."""

from django.db import transaction
from django.http import Http404
from django.core.exceptions import ValidationError as DjangoValidationError
from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from ...planning_models import PlanningEvent


def deliver_planning_events(*, event_kinds=None):
    from core_apps.notifications.services.notification_service import (
        NotificationService,
    )
    from .event_copy import event_copy
    from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

    delivered = 0
    retry_before = timezone.now() - timedelta(minutes=2)
    pending = PlanningEvent.objects.filter(
        delivered_at__isnull=True, attempts__lt=5, recipient__is_active=True
    )
    if event_kinds is not None:
        pending = pending.filter(destination__event_kind__in=event_kinds)
    for identifier in (
        pending.filter(Q(attempts=0) | Q(updated_at__lt=retry_before))
        .order_by("created_at")
        .values_list("id", flat=True)[:100]
    ):
        with transaction.atomic():
            event = (
                PlanningEvent.objects.select_for_update()
                .select_related("recipient")
                .get(id=identifier)
            )
            if event.delivered_at or not event.recipient.is_active:
                continue
            if event.attempts and event.updated_at >= retry_before:
                continue
            try:
                copy = event_copy(event)
            except (
                NotFound,
                Http404,
                PermissionDenied,
                ValidationError,
                DjangoValidationError,
                ValueError,
                TypeError,
                KeyError,
            ):
                event.delivered_at = timezone.now()
                event.delivery_status = "stale_or_unauthorized"
                event.save(
                    update_fields=["delivered_at", "delivery_status", "updated_at"]
                )
                continue
            if event.notification_id is None:
                event.notification = NotificationService.create_notification(
                    user=event.recipient,
                    title=copy.get("title")
                    or (
                        "تحديث من دعم سكون / Support update"
                        if event.destination.get("action_type") == "open_support_ticket"
                        else (
                            "تحديث بخصوص تقييم في سكون / Review update"
                            if event.destination.get("action_type")
                            in {
                                "open_reviews",
                                "open_review_opportunity",
                                "open_review_section",
                            }
                            else "تحديث بشأن طلب السكن / Housing update"
                        )
                    ),
                    body=copy.get("body")
                    or "افتح التطبيق لمراجعة التفاصيل / Open the app to review.",
                    category=copy.get("category", "housing_planning"),
                    notification_type=copy.get("notification_type", "general"),
                    data={
                        **event.destination,
                        "event_id": str(event.id),
                        "event_source": "planning",
                    },
                    send_push=False,
                )
            elif event.destination.get("event_kind") == "viewing_changed":
                event.notification.data = {
                    **event.notification.data,
                    **event.destination,
                    "presentation_workspace": event.destination["workspace"],
                }
                event.notification.scope = event.destination["workspace"]
                event.notification.save(update_fields=["data", "scope", "updated_at"])
            if event.destination.get("decision_id"):
                from ...models import ReviewModerationDecision
                from ..reputation.visibility import decision_notice

                decision = ReviewModerationDecision.objects.filter(
                    id=event.destination["decision_id"]
                ).first()
                if decision:
                    decision_notice(decision, event.recipient)
            from core_apps.notifications.services.push_delivery import (
                queue_notification,
            )

            queue_notification(event.notification)
            event.delivery_status = "push_queued"
            event.delivered_at = timezone.now()
            event.attempts += 1
            event.save()
            delivered += 1
    return delivered
