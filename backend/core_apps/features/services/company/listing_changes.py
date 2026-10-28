"""Immutable source invalidation without reversing company -> property lock order."""

from django.db.models import Q
from ...models import RentalAuditEvent
from ...company_models import CompanyBookingItem
from ...planning_models import PlanningEvent
from ..rental_lifecycle.common import audit
from ..rental_lifecycle.inventory import topology
from ..rental_phase2 import RentalConflict
from core_apps.properties.services.viewing_listing_changes import source_state

ACTION = "company_package_source_changed"
VISIBILITY_ACTION = "company_package_offer_visibility"
TERMINAL = {"withdrawn", "replaced", "rejected"}


def source(prop):
    facts = source_state(prop, "")
    return {
        "location": facts["location"],
        "accommodation": {
            "rooms": topology(prop.rental_inventory),
            "mode": (prop.rental_inventory or {}).get("mode", "whole"),
            "floor": prop.floor,
            "building_id": prop.building_id,
            "complex_id": prop.complex_id,
        },
        "capacity": prop.occupancy_capacity,
        "property_type": prop.property_type_id,
        "furnished": prop.is_furnished,
        "suitable_for": prop.suitable_for,
    }


def events(item, *, all_changes=False):
    return RentalAuditEvent.objects.filter(
        subject_kind="companybookingitem",
        subject_id=item.id,
        action__in=[ACTION, VISIBILITY_ACTION] if all_changes else [ACTION],
    ).order_by("created_at", "pk")


def needs_review(item):
    return bool(
        not item.lease_id
        and not item.invitation_id
        and item.status not in {"withdrawn", "replaced"}
        and events(item).exists()
    )


def publication_blocked(item):
    return bool(
        not item.lease_id
        and not item.invitation_id
        and item.status not in TERMINAL
        and item.offer.status != "published"
    )


def require_current(item):
    if needs_review(item):
        raise RentalConflict(
            "The accommodation changed. Review the history and replace this package.",
            code="company_source_changed",
        )


def history(item):
    return [
        {"id": str(row.id), "at": row.created_at.isoformat(), **row.metadata}
        for row in events(item, all_changes=True)
    ]


def propagate(prop, before):
    current = source(prop)
    changes = [
        {"field": key, "before": value, "after": current[key]}
        for key, value in before.items()
        if value != current[key]
    ]
    if not changes:
        return
    # The property is already locked. Commands acquire company/package before
    # property; append source facts without acquiring their locks in reverse.
    # Commands check this durable invalidation after locking current inventory.
    candidates = (
        CompanyBookingItem.objects.filter(
            snapshot__units__contains=[{"id": str(prop.id)}],
            lease__isnull=True,
            invitation__isnull=True,
        )
        .exclude(status__in=TERMINAL)
        .exclude(hold__status__in=["committed", "reconciliation_pending"])
        .select_related("request__company", "assigned_approver__user")
    )
    for item in candidates:
        event = audit(
            item,
            prop.owner,
            ACTION,
            metadata={
                "property_id": str(prop.id),
                "source_revision": prop.review_revision,
                "listing_changes": changes,
            },
        )
        notify(item, event)


def notify(item, event):
    recipients = {item.request.coordinator_id}
    if item.assigned_approver_id:
        recipients.add(item.assigned_approver.user_id)
    for recipient_id in recipients:
        PlanningEvent.objects.get_or_create(
            recipient_id=recipient_id,
            event_key=f"company.source:{event.id}",
            defaults={
                "destination": {
                    "action_type": "open_company_request",
                    "event_kind": event.action,
                    "target_id": str(item.request.id),
                    "company_id": str(item.request.company.id),
                    "company_role": (
                        "coordinator"
                        if recipient_id == item.request.coordinator_id
                        else "approver"
                    ),
                    "item_id": str(item.id),
                    "source_event_id": str(event.id),
                    "workspace": "company",
                    "schema_version": "1",
                }
            },
        )


def visibility_changed(offer, before):
    if before == offer.status:
        return
    for item in (
        CompanyBookingItem.objects.filter(
            offer=offer,
            lease__isnull=True,
            invitation__isnull=True,
        )
        .exclude(status__in=TERMINAL)
        .select_related("request__company", "assigned_approver__user")
    ):
        event = audit(
            item,
            offer.owner,
            VISIBILITY_ACTION,
            metadata={
                "portfolio_offer_id": str(offer.id),
                "source_revision": offer.revision,
                "listing_changes": [
                    {
                        "field": "availability",
                        "before": before == "published",
                        "after": offer.status == "published",
                    }
                ],
            },
        )
        notify(item, event)


def invalidated_ids():
    return RentalAuditEvent.objects.filter(
        subject_kind="companybookingitem", action=ACTION
    ).values("subject_id")


def live_budget(query):
    # Keep the ledger/audit row; it no longer authorizes a new commitment. An
    # existing agreement or unknown provider outcome retains its reservation.
    return query.exclude(
        Q(
            status="reserved",
            item__id__in=invalidated_ids(),
            item__lease__isnull=True,
            item__invitation__isnull=True,
        )
        & ~Q(item__hold__status__in=["committed", "reconciliation_pending"])
    )


def notification_copy(event):
    from django.shortcuts import get_object_or_404
    from rest_framework.exceptions import NotFound
    from .access import company_subject

    item = get_object_or_404(CompanyBookingItem, id=event.destination.get("item_id"))
    if (
        str(item.request.id) != event.destination.get("target_id")
        or str(item.request.company.id) != event.destination.get("company_id")
        or event.destination.get("workspace") != "company"
        or company_subject(event.recipient, item.id) is None
        or not events(item, all_changes=True)
        .filter(
            id=event.destination.get("source_event_id"),
            action=event.destination.get("event_kind"),
        )
        .exists()
    ):
        raise NotFound()
    if event.destination.get("event_kind") == VISIBILITY_ACTION:
        return {
            "title": "تغير نشر عرض المحفظة / Portfolio publication changed",
            "body": "راجع حالة العرض الحالية وسجل النشر قبل المتابعة. المهل والموافقات القائمة محفوظة. / Review the current publication status and history. Existing deadlines and approvals are preserved.",
        }
    return {
        "title": "تغير سكن الحزمة / Package accommodation changed",
        "body": "راجع الوحدة المتأثرة وسجل التغيير قبل المتابعة. العقود القائمة محفوظة. / Review the affected unit and history before proceeding. Existing contracts are preserved.",
    }
