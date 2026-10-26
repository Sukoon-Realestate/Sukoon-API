"""Corporate execution uses the ordinary mandate, review and invoice journeys."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from ...models import CompanyBookingItem
from ..company import contract_access, tenancy_access, bookings
from ..advanced_execution.progress import canonical_lease, outcome
from ..signing_documents import unresolved as unresolved_signature


def leg_payload(plan, leg, actor):
    terms = leg.specification["terms"]
    own = str(actor.id)
    booking = CompanyBookingItem.objects.select_related(
        "request__company", "offer__owner", "lease"
    ).get(id=leg.canonical_id)
    preparation = getattr(booking, "contract_preparation", None)
    lease = canonical_lease(leg)
    tenancy = getattr(lease, "company_tenancy", None) if lease else None
    coordinator = bool(
        booking.request.coordinator_id == actor.pk
        and booking.request.company.memberships.filter(
            user=actor, is_active=True, is_coordinator=True
        ).exists()
    )
    kind, identity = "", ""
    if tenancy and tenancy_access.roles(tenancy, actor):
        kind, identity = "company_tenancy", str(tenancy.id)
    elif preparation and contract_access.can_read(preparation, actor):
        kind, identity = "company_preparation", str(preparation.id)
    elif not preparation and coordinator and booking.status == "held":
        kind, identity = "company_prepare", str(booking.id)
    commercial = bool(lease and tenancy_access.commercial_read(lease, actor))
    employee = own in terms["employee_ids"] and not commercial
    state, unknown = outcome(leg, lease)
    return {
        "role": (
            "owner"
            if own == terms["owner_id"]
            else "employee" if employee else "company_authorizer"
        ),
        "company_name": terms["company_name"],
        "payer_kind": "organization",
        "provider_mode": "test",
        "actual_occupancy": bool(lease and lease.occupancy_status == "occupied"),
        "staff_are_not_personal_payers": True,
        "rent_minor": 0 if employee else terms["monthly_rent_minor"],
        "deposit_minor": 0 if employee else terms["deposit_minor"],
        "terms": (
            {}
            if employee
            else {
                key: terms[key]
                for key in (
                    "company_id",
                    "company_name",
                    "payer_kind",
                    "monthly_rent_minor",
                    "deposit_minor",
                    "currency",
                    "starts_on",
                    "ends_on_exclusive",
                )
            }
        ),
        "document_hash": lease.document_hash if commercial else "",
        "invoice_id": "",
        "invoice_revision": 0,
        "first_invoice_minor": None,
        "lease_id": str(lease.id) if commercial else "",
        "starts_on": terms["starts_on"],
        "ends_on_exclusive": terms["ends_on_exclusive"],
        "properties": [] if employee else terms["properties"],
        "own_placement": next(
            (
                {"property_id": row["property_id"], "title": row["title"]}
                for row in terms["placements"]
                if row["actor_id"] == own
            ),
            {},
        ),
        "continuation_kind": kind,
        "continuation_id": identity,
        "available_steps": [],
        "may_withdraw": coordinator
        and state not in {"confirmed", "withdrawn", "expired"},
        "can_withdraw": coordinator
        and not unknown
        and not (lease and unresolved_signature(lease))
        and state not in {"confirmed", "withdrawn", "expired"},
        "waiting_reason": "reconciliation_required" if unknown else "company_reviews",
    }


def withdraw(plan, actor, data):
    leg = get_object_or_404(plan.legs.select_for_update(), id=data.get("leg_id"))
    booking = CompanyBookingItem.objects.get(id=leg.canonical_id)
    if str(actor.id) not in leg.actor_ids or booking.request.coordinator_id != actor.pk:
        raise PermissionDenied(
            "Only the assigned coordinator can withdraw this company package."
        )
    from ..company.access import member_for

    member_for(actor, booking.request.company, "coordinate")
    lease = canonical_lease(leg)
    if lease:
        leg.lease = lease
        from ..advanced_execution.engine import withdraw_canonical

        return withdraw_canonical(plan, leg, actor)
    bookings.withdraw_item(
        actor,
        booking.id,
        {
            "expected_revision": booking.revision,
            "reason": "Explicit withdrawal of an uncommitted execution package.",
        },
    )
    leg.state = "withdrawn"
    leg.save(update_fields=["state", "updated_at"])
    from ..advanced_execution.plans import record_step
    from ..advanced_execution.progress import refresh

    record_step(
        plan,
        leg,
        "release_uncommitted",
        "confirmed",
        "company_booking",
        booking.id,
        actor=actor,
    )
    refresh(plan, persist=True)
    return plan
