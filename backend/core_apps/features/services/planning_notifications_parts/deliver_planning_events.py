"""Planning notifications: deliver planning events."""

from django.db import transaction
from django.http import Http404
from django.core.exceptions import ValidationError as DjangoValidationError
from datetime import timedelta
from uuid import UUID
from django.db.models import Q
from django.utils import timezone
from ...planning_models import PlanningEvent


_ALL_EVENTS = object()
_MAX_TARGETED_EVENTS = 100


def _selected_event_ids(value):
    if (
        not isinstance(value, (list, tuple))
        or not 1 <= len(value) <= _MAX_TARGETED_EVENTS
    ):
        raise ValueError(
            "event_ids must be a nonempty list or tuple of at most 100 UUIDs."
        )
    if any(not isinstance(identifier, (str, UUID)) for identifier in value):
        raise ValueError("event_ids must contain only UUIDs or UUID strings.")
    try:
        return tuple(UUID(str(identifier)) for identifier in value)
    except ValueError as error:
        raise ValueError("event_ids must contain only valid UUIDs.") from error


def deliver_planning_events(*, event_kinds=None, event_ids=_ALL_EVENTS):
    """Return the number delivered through the normal inbox and push queue.

    Omitting event_ids preserves the scheduled worker's general scan. An explicit
    selection must contain 1–100 UUIDs; invalid/None/empty input fails before any
    query. Selection intersects event_kinds and the ordinary due/authority guards;
    unknown or already handled IDs never fall back to general processing.
    Delivery enqueues PushDelivery as usual; this is not an inbox-only option.
    """
    if event_ids is not _ALL_EVENTS:
        event_ids = _selected_event_ids(event_ids)

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
    if event_ids is not _ALL_EVENTS:
        pending = pending.filter(id__in=event_ids)
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
