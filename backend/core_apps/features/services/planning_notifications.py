"""Durable, deduplicated planning notifications with recipient-scoped routes."""

from django.db import transaction
from datetime import timedelta
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from ..planning_models import PlanningEvent


def record_event(item, actor, operation):
    from ..models import RentalChange
    from ..planning_models import (
        RoommateConnection,
        HousingGroup,
        GroupJoinRequest,
        GroupProcess,
        HousingRequest,
        HousingOffer,
        ConditionReport,
        TenancyTransition,
    )

    recipients, action, target, workspace = [], "", item.id, "tenant"
    if isinstance(item, RoommateConnection):
        recipients, action = [item.first, item.second], "open_roommate_connections"
    elif isinstance(item, HousingGroup):
        recipients = [
            x.user
            for x in item.memberships.filter(status="active").select_related("user")
        ]
        action = "open_housing_group"
    elif isinstance(item, GroupJoinRequest):
        recipients = [item.user] + [
            x.user for x in item.group.memberships.filter(role="admin", status="active")
        ]
        # Pending applicants cannot read the group; they receive the join-request destination.
        action, target = "open_group_join_request", item.id
    elif isinstance(item, GroupProcess):
        recipients = [
            x.user
            for x in item.group.memberships.filter(
                status="active", user__id__in=item.participant_ids
            )
        ]
        action, target = "open_housing_group", item.group.id
    elif isinstance(item, HousingOffer):
        recipients, action, target = (
            [item.request.user, item.owner],
            "open_housing_request",
            item.request.id,
        )
    elif isinstance(item, HousingRequest):
        # Editing a request notifies only owners with an existing consented offer relationship.
        recipients = [x.owner for x in item.offers.select_related("owner")]
        action = "open_housing_request"
    elif isinstance(item, (ConditionReport, TenancyTransition, RentalChange)):
        recipients = [item.lease.owner, item.lease.tenant]
        action = (
            "open_rental_change"
            if isinstance(item, RentalChange)
            else (
                "open_condition_report"
                if isinstance(item, ConditionReport)
                else (
                    "open_move_out_notice"
                    if item.kind == "moveOutNotice"
                    else "open_replacement_request"
                )
            )
        )
    if not action:
        return
    for recipient in recipients:
        if recipient.pk == actor.pk or not recipient.is_active:
            continue
        data = {
            "action_type": action,
            "target_id": str(target),
            "schema_version": "1",
            "workspace": workspace,
        }
        if isinstance(item, (ConditionReport, TenancyTransition, RentalChange)):
            data["workspace"] = (
                "owner" if recipient.pk == item.lease.owner_id else "tenant"
            )
        if isinstance(item, RentalChange):
            data.update(
                lease_id=str(item.lease.id),
                change_id=str(item.id),
                change_kind=item.kind,
            )
        if isinstance(item, HousingOffer):
            data["workspace"] = "owner" if recipient.pk == item.owner_id else "tenant"
        PlanningEvent.objects.get_or_create(
            recipient=recipient,
            event_key=f"{operation}:{item.id}:{item.revision}",
            defaults={"destination": data},
        )
    if isinstance(item, HousingGroup):
        for process in item.processes.filter(status="under_review", kind="application"):
            PlanningEvent.objects.get_or_create(
                recipient=process.property.owner,
                event_key=f"group.application:{process.id}:{process.revision}",
                defaults={
                    "destination": {
                        "action_type": "open_group_applications",
                        "target_id": str(process.id),
                        "workspace": "owner",
                        "schema_version": "1",
                    }
                },
            )
    if (
        isinstance(item, TenancyTransition)
        and item.candidate_id
        and item.candidate.tenant_id != actor.pk
    ):
        PlanningEvent.objects.get_or_create(
            recipient=item.candidate.tenant,
            event_key=f"replacement.candidate:{item.id}:{item.revision}",
            defaults={
                "destination": {
                    "action_type": "open_replacement_invitations",
                    "target_id": str(item.id),
                    "workspace": "tenant",
                    "schema_version": "1",
                }
            },
        )


def record_lease_reminders():
    """One reminder per party and lease end date, independent of beat retries."""
    from ..models import Lease, RentalChange

    today = timezone.localdate()
    until = today + timedelta(days=max(0, settings.PLANNING_LEASE_REMINDER_DAYS))
    renewed_ids = RentalChange.objects.filter(
        kind=RentalChange.Kind.RENEWAL, status=RentalChange.Status.APPLIED
    ).values("lease_id")
    leases = (
        Lease.objects.filter(
            legacy_read_only=False,
            status=Lease.Status.ACTIVE,
            end_date__gt=today,
            end_date__lte=until,
        )
        .exclude(occupancy_status="returned")
        .exclude(pk__in=renewed_ids)
        .select_related("owner", "tenant")
    )
    created = 0
    for lease in leases.iterator():
        for user, workspace in ((lease.owner, "owner"), (lease.tenant, "tenant")):
            if not user.is_active:
                continue
            _, new = PlanningEvent.objects.get_or_create(
                recipient=user,
                event_key=f"lease.end:{lease.id}:{lease.end_date}",
                defaults={
                    "destination": {
                        "action_type": "open_rental_center",
                        "target_id": str(lease.id),
                        "lease_id": str(lease.id),
                        "workspace": workspace,
                        "schema_version": "1",
                    }
                },
            )
            created += int(new)
    return created


def deliver_planning_events():
    from core_apps.notifications.services.notification_service import (
        NotificationService,
    )
    from core_apps.notifications.services.fcm_service import FCMService
    from .planning_access import planning_subject
    from rest_framework.exceptions import NotFound

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
                if event.destination.get("event_kind") == "visit_post_decision":
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
                    from ..planning_condition_views import participant_lease

                    lease = participant_lease(
                        event.recipient, event.destination["lease_id"]
                    )
                    if lease.status != "active" or lease.occupancy_status == "returned":
                        raise NotFound()
                elif event.destination.get("action_type") == "open_rental_change":
                    from ..models import RentalChange
                    from ..planning_condition_views import participant_lease

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
                    from ..planning_models import TenancyTransition

                    if not TenancyTransition.objects.filter(
                        id=event.destination["target_id"],
                        candidate__tenant=event.recipient,
                        kind="replacement",
                        status="candidate_pending",
                    ).exists():
                        raise NotFound()
                else:
                    planning_subject(event.recipient, event.destination["target_id"])
            except NotFound:
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
