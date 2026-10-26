"""Physical changes invalidate only affected uncommitted corporate packages."""

# flake8: noqa: F401,F811
from copy import deepcopy
import pytest
from rest_framework.exceptions import NotFound
from .test_company_housing import company_setup, proposed, approved
from .test_rental_phase2 import rental_participants, authenticated
from .test_rental_lifecycle import policy
from .test_cycle_concurrency import parallel_calls
from core_apps.features.services.company import (
    bookings,
    listing_changes,
    approval_routing,
)
from core_apps.features.services.company.projections import company_payload
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.services.planning_notifications_parts.event_copy import (
    event_copy,
)
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.models import Lease, CompanyBudgetReservation
from core_apps.properties.models import Property
from core_apps.properties.services.property import PropertyService
from core_apps.properties.tests.test_viewing_listing_changes import edit_offer

pytestmark = pytest.mark.django_db


def republish(prop):
    Property.objects.filter(pk=prop.pk).update(status="verified", is_verified=True)


def test_source_history_blocks_old_approval_and_replacement_preserves_evidence(
    company_setup,
):
    item = approved(company_setup)
    previous = deepcopy(item.snapshot)
    prop = company_setup[5][0]
    PropertyService.update_property(prop, {"occupancy_capacity": 3})
    item.refresh_from_db()
    payload = bookings.item_payload(item)
    assert payload["source_review_required"] and payload["can_replace"]
    assert (
        not payload["contract_preparation_available"] and not payload["can_negotiate"]
    )
    assert payload["source_changes"][0]["listing_changes"] == [
        {"field": "capacity", "before": 4, "after": 3}
    ]
    assert item.snapshot == previous and item.approvals.count() == 1
    assert not bookings._live_reservations(item.request.company).exists()
    assert CompanyBudgetReservation.objects.get(item=item).status == "reserved"
    assert (
        company_payload(item.request.company, company_setup[1])["reserved_rent_minor"]
        == 0
    )
    assert (
        approval_routing.work_items(company_setup[1], item.request.company)
        .filter(pk=item.pk)
        .exists()
    )
    assert (
        approval_routing.work_items(company_setup[2], item.request.company)
        .filter(pk=item.pk)
        .exists()
    )
    assert (
        approval_routing.work_payload(item, company_setup[2])["action"]
        == "review_request"
    )
    republish(prop)
    with pytest.raises(RentalConflict) as error:
        bookings.hold_item(
            company_setup[1], item.id, {"expected_revision": item.revision}
        )
    assert error.value.get_codes() == "company_source_changed"
    request = item.request
    replacement = bookings.select_offer(
        company_setup[1],
        request.id,
        {
            "expected_revision": request.revision,
            "offer_id": item.offer.id,
            "offer_revision": item.offer.revision,
            "occupant_ids": [],
            "replaces_item_id": item.id,
            "replaces_item_revision": item.revision,
        },
    )
    item.refresh_from_db()
    assert item.status == "replaced" and replacement.replaces_id == item.pk
    assert (
        not listing_changes.needs_review(replacement)
        and replacement.snapshot["capacity"] == 7
    )
    assert item.approvals.get().snapshot == previous
    assert len(listing_changes.history(item)) == 1


def test_events_follow_current_coordinator_and_approver_authority(company_setup):
    item = approved(company_setup)
    prop = company_setup[5][0]
    PropertyService.update_property(prop, {"street": "New physical address"})
    events = list(
        PlanningEvent.objects.filter(destination__event_kind=listing_changes.ACTION)
    )
    assert {e.recipient_id for e in events} == {
        company_setup[1].pk,
        company_setup[2].pk,
    }
    assert all(event_copy(e) for e in events)
    deliver_planning_events(event_kinds=[listing_changes.ACTION])
    for event in events:
        event.refresh_from_db()
        assert event.notification.scope == "company"
        assert event.notification.data["target_id"] == str(item.request.id)
    reviewer = next(e for e in events if e.recipient_id == company_setup[2].pk)
    item.assigned_approver.is_active = False
    item.assigned_approver.save()
    with pytest.raises(NotFound):
        event_copy(reviewer)
    assert not approval_routing.work_payload(item, company_setup[2])["actionable"]


def test_editorial_or_individual_price_change_does_not_replace_portfolio_quote(
    company_setup,
):
    item = proposed(company_setup)
    prop = company_setup[5][0]
    price = item.snapshot["monthly_rent"]
    PropertyService.update_property(prop, {"title": "Edited display name"})
    prop.refresh_from_db()
    edit_offer(
        prop, terms={**prop.rental_inventory["offers"][0]["terms"], "price": "12000"}
    )
    republish(prop)
    assert not listing_changes.needs_review(item)
    result = bookings.decide(
        company_setup[2],
        item.id,
        {
            "expected_revision": item.revision,
            "snapshot_digest": item.snapshot_digest,
            "decision": "approved",
        },
    )
    assert result.status == "approved" and result.snapshot["monthly_rent"] == price


def test_existing_contract_keeps_signed_terms_and_budget(company_setup):
    item = approved(company_setup)
    prop = company_setup[5][0]
    lease = Lease.objects.create(
        property=prop,
        owner=company_setup[0],
        renter_company=item.request.company,
        status="active",
        start_date=item.request.starts_on,
        end_date=item.request.ends_on_exclusive,
        rent_amount_minor=100000,
        terms={"signed": "original"},
        template_id="company-rental",
        template_version="1",
    )
    item.lease = lease
    item.save()
    CompanyBudgetReservation.objects.filter(item=item).update(status="committed")
    PropertyService.update_property(prop, {"street": "New address"})
    assert not listing_changes.history(item) and not listing_changes.needs_review(item)
    assert bookings._live_reservations(item.request.company).count() == 1
    lease.refresh_from_db()
    assert lease.terms == {"signed": "original"}


@pytest.mark.django_db(transaction=True)
def test_concurrent_source_edit_and_approval_never_leave_reusable_old_consent(
    company_setup,
):
    item = proposed(company_setup)
    prop = company_setup[5][0]

    def run(index):
        if index == 0:
            PropertyService.update_property(prop, {"occupancy_capacity": 3})
            return None
        try:
            bookings.decide(
                company_setup[2],
                item.id,
                {
                    "expected_revision": item.revision,
                    "snapshot_digest": item.snapshot_digest,
                    "decision": "approved",
                },
            )
            return "approved"
        except RentalConflict as error:
            return error.get_codes()

    _, result = parallel_calls(run)
    assert result in {"approved", "authority_required", "company_source_changed"}
    item.refresh_from_db()
    assert listing_changes.needs_review(item)
    assert not bookings.item_payload(item)["contract_preparation_available"]
    assert not bookings._live_reservations(item.request.company).exists()
