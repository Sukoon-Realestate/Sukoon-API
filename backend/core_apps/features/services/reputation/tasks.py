"""Restart-safe generation/release/reminders, using the existing planning outbox."""

from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound
from ...models import Lease, ReviewCase, ReviewOpportunity, ReviewDraft
from core_apps.properties.models import PropertyVisitDecision
from .policy import ReviewError
from .generation import generate_viewing, generate_tenancy, generate_housemates, event
from .submission import release, opportunity_for
from .visibility import section_for, published, sections


def reconcile():
    counts = {
        "viewings": 0,
        "tenancies": 0,
        "housemates": 0,
        "blocked_sources": 0,
        "released": 0,
    }
    now = timezone.now()
    if getattr(settings, "REVIEWS_ENABLED", False):
        for decision in PropertyVisitDecision.objects.filter(
            attested_at__gte=now - timedelta(days=7)
        ).select_related("visit"):
            try:
                generate_viewing(decision.visit)
                counts["viewings"] += 1
            except ReviewError:
                counts["blocked_sources"] += 1
        ended = Lease.objects.filter(
            handovers__kind="move_out",
            handovers__status="accepted",
            handovers__accepted_at__gte=now - timedelta(days=30),
        ).distinct()
        for lease in ended:
            try:
                generate_tenancy(lease)
                counts["tenancies"] += 1
            except ReviewError:
                counts["blocked_sources"] += 1
            for peer in Lease.objects.filter(property_id=lease.property_id).exclude(
                tenant_id=lease.tenant_id
            ):
                try:
                    generate_housemates(lease, peer)
                    counts["housemates"] += 1
                except ReviewError:
                    pass
    if getattr(settings, "REVIEWS_ENABLED", False):
        from ...models import EmployeeAssignment, LeaseResponsibilityTransition
        from .company_generation import generate_employee

        for assignment in EmployeeAssignment.objects.filter(
            occupancy_confirmations__kind="departure",
            occupancy_confirmations__state="accepted",
            occupancy_confirmations__accepted_at__gte=now - timedelta(days=30),
        ).distinct():
            try:
                generate_employee(assignment)
            except ReviewError:
                counts["blocked_sources"] += 1
        for change in LeaseResponsibilityTransition.objects.filter(
            state="accepted", accepted_at__gte=now - timedelta(days=30)
        ):
            try:
                generate_tenancy(change.lease)
            except ReviewError:
                counts["blocked_sources"] += 1
    for identity in ReviewCase.objects.filter(
        gate_released_at__isnull=True, closes_at__lte=now
    ).values_list("id", flat=True):
        with transaction.atomic():
            case = ReviewCase.objects.select_for_update().get(id=identity)
            release(case)
            counts["released"] += int(bool(case.gate_released_at))
    ReviewOpportunity.objects.filter(state="open", case__closes_at__lte=now).update(
        state="expired"
    )
    ReviewDraft.objects.filter(
        opportunity__case__closes_at__lte=now - timedelta(days=7)
    ).delete()
    if getattr(settings, "REVIEWS_ENABLED", False):
        for opp in ReviewOpportunity.objects.filter(
            state="open",
            reminders_enabled=True,
            submitted_once_at__isnull=True,
            case__closes_at__gt=now,
        ).select_related("case", "reviewer"):
            half = opp.case.opens_at + (opp.case.closes_at - opp.case.opens_at) / 2
            for name, threshold in [
                ("midpoint", half),
                ("48h", opp.case.closes_at - timedelta(hours=48)),
            ]:
                if now >= threshold:
                    if opp.reviewer_company_id:
                        from .company_authority import recipients

                        for user in recipients(
                            opp.case.company_binding, opp.reviewer_company, submit=True
                        ):
                            event(opp, user, "review_reminder", name)
                    else:
                        event(opp, opp.reviewer, "review_reminder", name)
    return counts


def authorize_notification(item):
    identity = item.destination.get("target_id")
    kind = item.destination.get("review_event")
    if kind in {"review_opportunity_opened", "review_reminder"}:
        opp = opportunity_for(item.recipient, identity)
        if kind == "review_reminder" and (
            opp.state != "open"
            or not opp.reminders_enabled
            or opp.case.closes_at <= timezone.now()
        ):
            raise NotFound()
        return
    section_for(item.recipient, identity)
