"""Actual PostgreSQL revisions, participant reviews and competing commands."""

import pytest
from datetime import timedelta
from django.db import connection
from django.utils import timezone
from core_apps.features.company_models import CompanyBudgetReservation
from core_apps.features.models import Lease, ReservationHold, RentalInventoryDayLock
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.company import bookings, contract_snapshot
from core_apps.features.services.rental_phase2 import RentalConflict
from .test_company_housing import company_setup, proposed, approved, API, command
from .test_company_request_correction import body
from .test_company_contract_preparation import cycle, create, authenticated
from .test_rental_phase2 import rental_participants
from .test_rental_lifecycle import policy
from .test_cycle_concurrency import parallel_calls


def edit(setup, **changes):
    request = setup[-1]
    request.refresh_from_db()
    return bookings.update_request(setup[1], request.id, body(request, **changes))


@pytest.mark.django_db
def test_metadata_and_larger_budget_preserve_approved_package(company_setup):
    item = approved(company_setup)
    original = item.snapshot.copy()
    request = edit(
        company_setup, title="Revised title", commitment_ceiling_minor=2000000
    )
    item.refresh_from_db()
    assert request.id == company_setup[-1].id
    assert request.commercial_revision == 2
    assert request.versions.count() == 2
    assert request.versions.get(version=2).changes["title"]["to"] == "Revised title"
    assert item.status == "approved"
    assert item.request_version == 1
    assert item.snapshot == original
    assert item.approvals.count() == 1
    assert CompanyBudgetReservation.objects.get(item=item).status == "reserved"


@pytest.mark.django_db
def test_material_change_preserves_history_and_requires_new_approval(company_setup):
    item = approved(company_setup)
    original = item.snapshot.copy()
    request = edit(company_setup, purpose="Different occupants' purpose")
    item.refresh_from_db()
    assert item.status == "request_changed"
    assert item.request_review_version == 2
    assert item.snapshot == original and item.approvals.count() == 1
    assert CompanyBudgetReservation.objects.get(item=item).status == "released"
    assert request.versions.get(version=2).affected_item_ids == [str(item.id)]
    with pytest.raises(RentalConflict):
        bookings.hold_item(
            company_setup[1], item.id, {"expected_revision": item.revision}
        )
    offer = company_setup[-2]
    replacement = bookings.select_offer(
        company_setup[1],
        request.id,
        {
            "expected_revision": request.revision,
            "offer_id": offer.id,
            "offer_revision": offer.revision,
            "occupant_ids": [],
            "replaces_item_id": item.id,
            "replaces_item_revision": item.revision,
        },
    )
    item.refresh_from_db()
    assert item.status == "replaced"
    assert replacement.replaces_id == item.pk
    assert replacement.request_version == 2
    assert replacement.status == "proposed" and not replacement.approvals.exists()
    assert replacement.snapshot["purpose"] == request.purpose
    assert item.approvals.first().snapshot == original
    assert bookings.item_payload(item)["replacement_item_id"] == str(replacement.id)


@pytest.mark.django_db
def test_smaller_budget_affects_only_packages_outside_new_limit(company_setup):
    item = approved(company_setup)
    request = edit(
        company_setup, commitment_ceiling_minor=item.full_term_rent_minor + 1
    )
    item.refresh_from_db()
    assert item.status == "approved"
    assert request.versions.get(version=2).affected_item_ids == []
    edit(company_setup, commitment_ceiling_minor=item.full_term_rent_minor - 1)
    item.refresh_from_db()
    assert item.status == "request_changed"


@pytest.mark.django_db
def test_existing_lease_and_financial_reservation_are_not_rewritten(company_setup):
    item = approved(company_setup)
    request = item.request
    lease = Lease.objects.create(
        property=company_setup[5][0],
        owner=company_setup[0],
        renter_company=request.company,
        status="active",
        start_date=request.starts_on,
        end_date=request.ends_on_exclusive,
        rent_amount_minor=100000,
        terms={"signed": "original"},
        template_id="company-rental",
        template_version="1",
    )
    item.lease = lease
    item.save()
    CompanyBudgetReservation.objects.filter(item=item).update(status="committed")
    request = edit(company_setup, purpose="New need", commitment_ceiling_minor=1)
    item.refresh_from_db()
    lease.refresh_from_db()
    assert item.request_review_version is None and item.status == "approved"
    assert lease.terms == {"signed": "original"}
    assert CompanyBudgetReservation.objects.get(item=item).status == "committed"
    assert request.versions.get(version=2).preserved_item_ids == [str(item.id)]


@pytest.mark.django_db
def test_unaffected_preparation_stays_valid_and_recipient_workspace_is_explicit(cycle):
    preparation = create(cycle)
    item = cycle["item"]
    original = preparation.snapshot.copy()
    request = item.request
    request.refresh_from_db()
    bookings.update_request(
        cycle["coordinator"], request.id, body(request, title="Display name only")
    )
    preparation.refresh_from_db()
    contract_snapshot.revalidate(preparation)
    assert preparation.snapshot == original
    events = PlanningEvent.objects.filter(
        event_key__startswith=f"company.contract:{preparation.id}:"
    )
    assert events.get(recipient=cycle["owner"]).destination["workspace"] == "owner"
    assert all(
        e.destination["workspace"] == "company"
        for e in events.exclude(recipient=cycle["owner"])
    )
    request.refresh_from_db()
    bookings.update_request(
        cycle["coordinator"], request.id, body(request, purpose="Changed purpose")
    )
    preparation.refresh_from_db()
    assert preparation.state == "changes_requested" and preparation.snapshot == original
    assert preparation.consents.exists()
    with pytest.raises(RentalConflict):
        contract_snapshot.revalidate(preparation)


@pytest.mark.django_db
def test_failed_replacement_keeps_hold_and_old_package(company_setup):
    item = approved(company_setup)
    prop = company_setup[5][0]
    hold = ReservationHold.objects.create(
        property=prop,
        actor=company_setup[1],
        offer_id=str(item.offer.id),
        offer_revision=item.offer.revision,
        inventory_revision=1,
        starts_on=item.request.starts_on,
        ends_on_exclusive=item.request.ends_on_exclusive,
        blocked_until_exclusive=item.request.ends_on_exclusive,
        expires_at=timezone.now() + timedelta(hours=1),
        status="active",
        selection_snapshot=item.snapshot,
        terms_digest=item.snapshot_digest,
        policy_version="synthetic",
        policy_snapshot={},
    )
    item.hold = hold
    item.status = "held"
    item.save()
    request = edit(company_setup, purpose="Changed")
    item.refresh_from_db()
    assert hold.status == "active"
    assert bookings.item_payload(item)["can_replace"] is False
    with pytest.raises(RentalConflict):
        bookings.select_offer(
            company_setup[1],
            request.id,
            {
                "expected_revision": request.revision,
                "offer_id": item.offer.id,
                "offer_revision": 0,
                "occupant_ids": [],
                "replaces_item_id": item.id,
                "replaces_item_revision": item.revision,
            },
        )
    item.refresh_from_db()
    hold.refresh_from_db()
    assert item.status == "request_changed" and hold.status == "active"
    assert not hasattr(item, "replacement")


@pytest.mark.django_db(transaction=True)
def test_two_edits_share_one_current_revision_and_history(company_setup):
    assert connection.vendor == "postgresql"
    request = company_setup[-1]
    data = [body(request, purpose=f"revision {i}") for i in range(2)]
    results = parallel_calls(
        lambda index: authenticated(
            company_setup[1], role="coordinator", company=company_setup[3]
        ).post(
            API + f"company-housing-requests/{request.id}/", data[index], format="json"
        )
    )
    assert sorted(r.status_code for r in results) == [200, 409]
    request.refresh_from_db()
    assert request.commercial_revision == 2 and request.versions.count() == 2


@pytest.mark.django_db(transaction=True)
def test_concurrent_approval_cannot_survive_material_request_edit(company_setup):
    item = proposed(company_setup)
    request = company_setup[-1]
    request.refresh_from_db()
    update = body(request, purpose="Changed while reviewer was looking")
    approval = command(
        expected_revision=item.revision,
        snapshot_digest=item.snapshot_digest,
        decision="approved",
    )
    responses = parallel_calls(
        lambda index: authenticated(
            company_setup[1] if index == 0 else company_setup[2],
            role="coordinator" if index == 0 else "approver",
            company=company_setup[3],
        ).post(
            API
            + (
                f"company-housing-requests/{request.id}/"
                if index == 0
                else f"company-booking-items/{item.id}/decide/"
            ),
            update if index == 0 else approval,
            format="json",
        )
    )
    assert responses[0].status_code == 200
    assert responses[1].status_code in {200, 409}
    item.refresh_from_db()
    assert item.status == "request_changed"
    assert not CompanyBudgetReservation.objects.filter(
        item=item, status="reserved"
    ).exists()
