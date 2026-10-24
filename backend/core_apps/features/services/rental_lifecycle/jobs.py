"""Idempotent local deadlines; no automatic financial or legal decisions."""

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from ...models import RentalOperationalCase, RentalInterest, ReservationHold
from .common import audit
from .notifications import record_rental_event


def reconcile_lifecycle_deadlines():
    now = timezone.now()
    escalated = 0
    for identifier in (
        RentalOperationalCase.objects.exclude(status__in=["resolved", "closed"])
        .filter(due_at__lte=now, escalated_at__isnull=True)
        .order_by("due_at")
        .values_list("pk", flat=True)[:100]
    ):
        with transaction.atomic():
            item = RentalOperationalCase.objects.select_for_update().get(pk=identifier)
            if item.escalated_at or item.status in {"resolved", "closed"}:
                continue
            item.escalated_at, item.severity = now, "high"
            item.revision += 1
            item.save()
            audit(
                item,
                None,
                "case.escalated",
                "The responsible team must resolve the missed deadline.",
            )
            if item.assigned_to:
                record_rental_event(
                    item, {item.assigned_to}, "case.escalated", "open_rental_case"
                )
            escalated += 1
    reminded = 0
    for item in (
        RentalInterest.objects.exclude(status__in=["withdrawn", "rejected", "invited"])
        .filter(response_due_at__lte=now)
        .filter(Q(shared_allocation__isnull=True) | Q(shared_allocation__proposal__plan__status="handed_off"))
        .select_related("tenant", "property__owner")[:100]
    ):
        actor = item.tenant if item.waiting_for == "tenant" else item.property.owner
        record_rental_event(
            item, {actor}, "application.response_due", "open_rental_interest"
        )
        reminded += 1
    return {"escalated_cases": escalated, "application_reminders": reminded}
