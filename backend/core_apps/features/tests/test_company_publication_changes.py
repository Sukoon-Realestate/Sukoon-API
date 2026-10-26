"""Publication blocks new follow-up, preserving the exact unexpired quote."""

# flake8: noqa: F401,F811
from copy import deepcopy
import pytest
from django.utils import timezone
from core_apps.features.models import CompanyBudgetReservation
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.company import (
    bookings,
    approval_routing,
    listing_changes,
)
from core_apps.features.services.company import contract_snapshot, contract_projection
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.services.planning_notifications import deliver_planning_events
from .test_company_housing import (
    company_setup,
    rental_participants,
    policy,
    proposed,
    approved,
    command,
    authenticated,
    API,
)
from .test_company_contract_preparation import cycle, create
from .test_company_negotiation import start, act, reapprove
from .test_cycle_concurrency import parallel_calls

pytestmark = pytest.mark.django_db


def publication(owner, offer, action, body=None):
    offer.refresh_from_db()
    data = body or command(expected_revision=offer.revision)
    result = authenticated(owner).post(
        API + f"portfolio-offers/{offer.id}/{action}/", data, format="json"
    )
    assert result.status_code == 200, result.data
    return data, result


def test_pause_replay_and_republish_preserve_approval_deadline_and_budget(
    company_setup,
):
    item = approved(company_setup)
    snapshot, deadline, revision = (
        deepcopy(item.snapshot),
        item.quote_expires_at,
        item.revision,
    )
    approval = item.approvals.get()
    data, result = publication(company_setup[0], item.offer, "pause")
    _, replay = publication(company_setup[0], item.offer, "pause", data)
    assert result.data == replay.data
    item.refresh_from_db()
    payload = bookings.item_payload(item)
    assert payload["publication_blocked"] and not payload["source_review_required"]
    assert (
        not payload["can_negotiate"] and not payload["contract_preparation_available"]
    )
    work = approval_routing.work_payload(item, company_setup[1])
    assert (
        not work["actionable"]
        and work["blocking_reason"] == "portfolio_offer_unpublished"
    )
    assert len(payload["source_changes"]) == 1
    assert payload["source_changes"][0]["portfolio_offer_id"] == str(item.offer.id)
    assert item.approvals.get().pk == approval.pk
    assert CompanyBudgetReservation.objects.get(item=item).status == "reserved"
    publication(company_setup[0], item.offer, "publish")
    item.refresh_from_db()
    assert item.revision == revision and item.quote_expires_at == deadline
    assert item.snapshot == snapshot and item.approvals.count() == 1
    assert not bookings.item_payload(item)["publication_blocked"]
    assert bookings.item_payload(item)["contract_preparation_available"]
    assert [
        row["listing_changes"][0]["after"] for row in listing_changes.history(item)
    ] == [False, True]
    deliver_planning_events(event_kinds=[listing_changes.VISIBILITY_ACTION])
    events = PlanningEvent.objects.filter(
        destination__event_kind=listing_changes.VISIBILITY_ACTION
    )
    assert events.count() == 4
    assert all(e.notification and e.notification.scope == "company" for e in events)


def test_pending_approval_requires_current_publication_and_same_quote_after_resume(
    company_setup,
):
    item = proposed(company_setup)
    publication(company_setup[0], item.offer, "pause")
    decision = {
        "expected_revision": item.revision,
        "snapshot_digest": item.snapshot_digest,
        "decision": "approved",
    }
    with pytest.raises(RentalConflict) as error:
        bookings.decide(company_setup[2], item.id, decision)
    assert error.value.get_codes() == "portfolio_offer_unpublished"
    assert not item.approvals.exists()
    publication(company_setup[0], item.offer, "publish")
    result = bookings.decide(company_setup[2], item.id, decision)
    assert result.status == "approved" and result.snapshot == item.snapshot
    assert result.quote_expires_at == item.quote_expires_at


def test_prepared_contract_keeps_its_reviewed_snapshot_after_republication(cycle):
    prepared = create(cycle)
    before = deepcopy(prepared.snapshot)
    revision = prepared.revision
    publication(cycle["owner"], cycle["item"].offer, "pause")
    projection = contract_projection.payload(prepared, cycle["coordinator"])
    assert "portfolio_offer_unpublished" in projection["blocking_reasons"]
    publication(cycle["owner"], cycle["item"].offer, "publish")
    contract_snapshot.revalidate(prepared)
    prepared.refresh_from_db()
    assert prepared.snapshot == before and prepared.revision == revision


def test_private_agreement_remains_exact_and_expiry_is_not_extended(cycle):
    agreement, _, _ = start(cycle)
    assert act(cycle, agreement, "owner", "accept").status_code == 200
    item = reapprove(cycle)
    prepared = create(cycle)
    before, deadline = deepcopy(item.snapshot), item.quote_expires_at
    publication(cycle["owner"], item.offer, "pause")
    publication(cycle["owner"], item.offer, "publish")
    item.refresh_from_db()
    assert item.snapshot == before and item.quote_expires_at == deadline
    contract_snapshot.revalidate(prepared)
    # An expired quote cannot be revived by publication even if its approval remains.
    type(item).objects.filter(pk=item.pk).update(quote_expires_at=timezone.now())
    publication(cycle["owner"], item.offer, "pause")
    publication(cycle["owner"], item.offer, "publish")
    with pytest.raises(RentalConflict) as error:
        bookings.hold_item(
            cycle["coordinator"], item.id, {"expected_revision": item.revision}
        )
    assert error.value.get_codes() == "approval_required"


@pytest.mark.django_db(transaction=True)
def test_concurrent_publication_pause_and_approval_leaves_followup_blocked(
    company_setup,
):
    item = proposed(company_setup)

    def run(index):
        if index == 0:
            publication(company_setup[0], item.offer, "pause")
            return "paused"
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
    assert result in {"approved", "portfolio_offer_unpublished"}
    item.refresh_from_db()
    assert bookings.item_payload(item)["publication_blocked"]
    assert item.approvals.count() <= 1
