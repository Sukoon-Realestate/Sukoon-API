"""Planning notifications: deliver planning events."""

from django.db import transaction
from django.http import Http404
from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from ...planning_models import PlanningEvent


def deliver_planning_events(*, event_kinds=None):
    from core_apps.notifications.services.notification_service import (
        NotificationService,
    )
    from core_apps.notifications.services.fcm_service import FCMService
    from ..planning_access import planning_subject
    from rest_framework.exceptions import NotFound, PermissionDenied

    delivered = 0
    retry_before = timezone.now() - timedelta(minutes=2)
    pending = PlanningEvent.objects.filter(delivered_at__isnull=True, attempts__lt=5)
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
                from ..rent_payment_reminders import (
                    EVENT_KINDS,
                    authorize,
                    notification_copy,
                )

                rent_reminder = event.destination.get("event_kind") in EVENT_KINDS
                copy = {}
                if rent_reminder:
                    copy = notification_copy(event)
                elif event.destination.get("action_type") == "open_search_alert":
                    from ...models import SearchAlert

                    if not SearchAlert.objects.filter(
                        id=event.destination.get("target_id"),
                        user=event.recipient,
                        revision=event.destination.get("revision"),
                        enabled=True,
                        deleted_at__isnull=True,
                    ).exists():
                        raise NotFound()
                elif event.destination.get("event_kind") == "viewing_changed":
                    from core_apps.properties.models import PropertyVisit
                    from core_apps.properties.services.viewing_access import can_read

                    visit = PropertyVisit.objects.filter(
                        id=event.destination.get("visit_id"),
                        revision=event.destination.get("revision"),
                    ).first()
                    if not visit or not can_read(visit, event.recipient):
                        raise NotFound()
                elif event.destination.get("action_type") == "open_support_ticket":
                    from core_apps.support.services import get_ticket_detail
                    from core_apps.support.models import Ticket

                    try:
                        get_ticket_detail(
                            event.recipient,
                            event.destination["target_id"],
                            workspace=event.destination.get("workspace"),
                        )
                    except Ticket.DoesNotExist as error:
                        raise NotFound() from error
                elif event.destination.get("action_type") in {
                    "open_reviews",
                    "open_review_opportunity",
                    "open_review_section",
                }:
                    from ..reputation.tasks import authorize_notification

                    authorize_notification(event)
                elif event.destination.get("action_type") == "open_company_tenancy":
                    from ..company.tenancy_access import get

                    get(event.recipient, event.destination["target_id"])
                elif event.destination.get("action_type") == "open_company_contract":
                    from ..company.contract_access import get

                    get(event.recipient, event.destination["target_id"])
                elif event.destination.get("action_type") == "open_company_mandates":
                    from ..company.mandates import authorize

                    authorize(event.recipient, event.destination["mandate_id"])
                elif event.destination.get("action_type") == "open_company_work":
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
                elif event.destination.get("event_kind") == "company_viewing_decision":
                    from core_apps.properties.models import PropertyVisitDecision
                    from core_apps.properties.services.viewing_access import can_read
                    from ..company.viewing_handoff import validate_source
                    from ..rental_phase2 import RentalConflict

                    decision = (
                        PropertyVisitDecision.objects.select_related(
                            "visit__property", "visit__tenant"
                        )
                        .filter(
                            id=event.destination.get("source_decision_id"),
                            visit__id=event.destination.get("target_id"),
                            visit__company__id=event.destination.get("company_id"),
                            visit__company__memberships__user=event.recipient,
                            visit__company__memberships__is_active=True,
                            visit__company__memberships__is_coordinator=True,
                        )
                        .first()
                    )
                    if not decision or not can_read(decision.visit, event.recipient):
                        raise NotFound()
                    try:
                        validate_source(decision.visit, decision)
                    except RentalConflict:
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
                    data={**event.destination, "event_id": str(event.id)},
                    send_push=False,
                )
            if event.destination.get("decision_id"):
                from ...models import ReviewModerationDecision
                from ..reputation.visibility import decision_notice

                decision = ReviewModerationDecision.objects.filter(
                    id=event.destination["decision_id"]
                ).first()
                if decision:
                    decision_notice(decision, event.recipient)
            event.delivery_status = "attempting"
            event.attempts += 1
            event.save()
        # The external call is outside the database transaction. Event ID deduplicates delivery.
        try:
            if rent_reminder:
                # A payment/authority change after enqueueing must not dispatch
                # a stale financial instruction. Push copy remains private.
                authorize(event)
            sent = FCMService.send_push_to_user(
                user=event.recipient,
                title=event.notification.title,
                body=event.notification.body,
                data=event.notification.data,
                notification_type=event.notification.notification_type,
            )
            # FCM reports delivery failures as zero as well as exceptions. Keep
            # the durable event pending when an eligible active device exists.
            from core_apps.notifications.models import DeviceToken

            if (
                sent == 0
                and FCMService.should_send_to_user(
                    event.recipient, event.notification.notification_type
                )
                and DeviceToken.objects.filter(
                    user=event.recipient, is_active=True
                ).exists()
            ):
                PlanningEvent.objects.filter(
                    pk=event.pk, delivered_at__isnull=True
                ).update(delivery_status="retry_pending")
                continue
        except (NotFound, Http404, PermissionDenied):
            PlanningEvent.objects.filter(pk=event.pk, delivered_at__isnull=True).update(
                delivered_at=timezone.now(), delivery_status="stale_or_unauthorized"
            )
            continue
        except Exception:
            PlanningEvent.objects.filter(pk=event.pk, delivered_at__isnull=True).update(
                delivery_status="retry_pending"
            )
            continue
        PlanningEvent.objects.filter(pk=event.pk, delivered_at__isnull=True).update(
            delivered_at=timezone.now(),
            delivery_status="provider_accepted" if sent else "no_delivery",
            provider_accepted_at=timezone.now() if sent else None,
        )
        delivered += 1
    return delivered
