"""Planning notifications: record event."""

from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from ...planning_models import PlanningEvent


def record_event(item, actor, operation):
    from ...models import RentalChange
    from ...planning_models import (
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
    from ...models import Lease, RentalChange

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
        parties = [(lease.owner, "owner"), (lease.tenant, "tenant")]
        if lease.renter_company_id:
            from ..company.tenancy_access import roles

            item = lease.company_tenancy
            coordinator = item.coordinator
            parties = [(lease.owner, "owner")]
            if "coordinator" in roles(item, coordinator):
                parties.append((coordinator, "tenant"))
        for user, workspace in parties:
            if not user or not user.is_active:
                continue
            _, new = PlanningEvent.objects.get_or_create(
                recipient=user,
                event_key=f"lease.end:{lease.id}:{lease.end_date}",
                defaults={
                    "destination": {
                        "action_type": (
                            "open_company_tenancy"
                            if lease.renter_company_id
                            else "open_rental_center"
                        ),
                        "target_id": (
                            str(lease.company_tenancy.id)
                            if lease.renter_company_id
                            else str(lease.id)
                        ),
                        "lease_id": str(lease.id),
                        "workspace": workspace,
                        "schema_version": "1",
                    }
                },
            )
            created += int(new)
    return created
