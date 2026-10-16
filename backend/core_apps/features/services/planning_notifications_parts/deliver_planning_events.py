"""Planning notifications: deliver planning events."""

from django.db import transaction
from django.http import Http404
from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from ...planning_models import PlanningEvent


def deliver_planning_events():
    from core_apps.notifications.services.notification_service import (
        NotificationService,
    )
    from core_apps.notifications.services.fcm_service import FCMService
    from ..planning_access import planning_subject
    from rest_framework.exceptions import NotFound, PermissionDenied

    delivered = 0
    retry_before = timezone.now() - timedelta(minutes=2)
    for identifier in (
        PlanningEvent.objects.filter(delivered_at__isnull=True, attempts__lt=5)
        .filter(Q(attempts=0) | Q(updated_at__lt=retry_before))
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
                if event.destination.get("action_type") == "open_company_work":
                    from ..company.access import company_for
                    from ..company.approval_routing import work_items

                    company = company_for(
                        event.recipient, event.destination["target_id"]
                    )
                    if (
                        not work_items(event.recipient, company)
                        .filter(
                            id=event.destination.get("item_id"),
                            revision=event.destination.get("revision"),
                        )
                        .exists()
                    ):
                        raise NotFound()
                elif event.destination.get("rental_lifecycle"):
                    from ..rental_foundation import get_authorized_rental_subject

                    item = get_authorized_rental_subject(
                        event.recipient, event.destination["target_id"]
                    )
                    if getattr(item, "revision", 1) != event.destination.get(
                        "revision"
                    ):
                        raise NotFound()
                elif event.destination.get("event_kind") == "visit_post_decision":
                    from core_apps.properties.models import PropertyVisitDecision

                    if (
                        event.destination.get("target_id")
                        != event.destination.get("visit_id")
                        or not PropertyVisitDecision.objects.filter(
                            id=event.destination.get("source_decision_id"),
                            visit__id=event.destination.get("visit_id"),
                            owner=event.recipient,
                            visit__property__owner=event.recipient,
                        ).exists()
                    ):
                        raise NotFound()
                elif event.destination.get("action_type") == "open_rental_center":
                    from ...planning_condition_views import participant_lease

                    lease = participant_lease(
                        event.recipient, event.destination["lease_id"]
                    )
                    if lease.status != "active" or lease.occupancy_status == "returned":
                        raise NotFound()
                elif event.destination.get("action_type") == "open_rental_change":
                    from ...models import RentalChange
                    from ...planning_condition_views import participant_lease

                    lease = participant_lease(
                        event.recipient, event.destination["lease_id"]
                    )
                    if not RentalChange.objects.filter(
                        id=event.destination["target_id"], lease=lease
                    ).exists():
                        raise NotFound()
                elif (
                    event.destination.get("action_type")
                    == "open_replacement_invitations"
                ):
                    from ...planning_models import TenancyTransition

                    if not TenancyTransition.objects.filter(
                        id=event.destination["target_id"],
                        candidate__tenant=event.recipient,
                        kind="replacement",
                        status="candidate_pending",
                    ).exists():
                        raise NotFound()
                else:
                    planning_subject(event.recipient, event.destination["target_id"])
            except (NotFound, Http404, PermissionDenied):
                event.delivered_at = timezone.now()
                event.save(update_fields=["delivered_at", "updated_at"])
                continue
            if event.notification_id is None:
                event.notification = NotificationService.create_notification(
                    user=event.recipient,
                    title="تحديث بشأن طلب السكن / Housing update",
                    body="افتح التطبيق لمراجعة التفاصيل / Open the app to review.",
                    category="housing_planning",
                    data={**event.destination, "event_id": str(event.id)},
                    send_push=False,
                )
            event.attempts += 1
            event.save()
        # The external call is outside the database transaction. Event ID deduplicates delivery.
        try:
            sent = FCMService.send_push_to_user(
                user=event.recipient,
                title=event.notification.title,
                body=event.notification.body,
                data=event.notification.data,
                notification_type="general",
            )
            # FCM reports delivery failures as zero as well as exceptions. Keep
            # the durable event pending when an eligible active device exists.
            from core_apps.notifications.models import DeviceToken

            if (
                sent == 0
                and FCMService.should_send_to_user(event.recipient, "general")
                and DeviceToken.objects.filter(
                    user=event.recipient, is_active=True
                ).exists()
            ):
                continue
        except Exception:
            continue
        PlanningEvent.objects.filter(pk=event.pk, delivered_at__isnull=True).update(
            delivered_at=timezone.now()
        )
        delivered += 1
    return delivered
