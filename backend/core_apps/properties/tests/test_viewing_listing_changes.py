"""Listing impact preserves exact inventory, visited history and special terms."""

# flake8: noqa: F401,F811 -- pytest fixtures are injected by name.
from copy import deepcopy
import uuid
import pytest
from core_apps.features.tests.test_rental_phase2 import (
    rental_participants,
    authenticated,
)
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.tests.test_group_process_history import reviewed_visit
from core_apps.properties.services.property import PropertyService
from core_apps.properties.services.viewing_commands import command
from core_apps.properties.models import PropertyVisit
from .test_viewing_event_history import request_visit

pytestmark = pytest.mark.django_db


def edit_offer(prop, **changes):
    prop.refresh_from_db()
    inventory = deepcopy(prop.rental_inventory)
    inventory["revision"] += 1
    offer = inventory["offers"][0]
    offer.update(changes)
    offer["revision"] += 1
    return PropertyService.update_property(prop, {"rental_inventory": inventory})


def test_price_edit_keeps_confirmed_visit_snapshot_and_notifies_both_parties(
    rental_participants,
):
    owner, tenant, _, prop, _ = rental_participants
    visit = request_visit(rental_participants)
    visit = command(owner, visit.id, {"expected_revision": 1, "action": "accept"})
    original = deepcopy(visit.offer_snapshot)
    prop = edit_offer(prop, terms={"price": "12000", "price_period": "monthly"})
    visit.refresh_from_db()
    assert prop.status == "under_review" and not prop.is_verified
    assert visit.status == "confirmed" and visit.offer_snapshot == original
    assert visit.change_history[-1]["listing_changes"] == [
        {"field": "price", "before": "10000", "after": "12000"}
    ]
    assert visit.change_history[-1]["reason_code"] == "terms_changed"
    rows = PlanningEvent.objects.filter(
        destination__visit_id=str(visit.id), destination__change="listing_changed"
    )
    assert {row.recipient_id: row.destination["workspace"] for row in rows} == {
        owner.pk: "owner",
        tenant.pk: "individual",
    }
    assert all(row.destination["target_id"] == str(visit.id) for row in rows)
    response = authenticated(tenant).get(
        f"/api/v1/properties/visits/requests/{visit.id}/"
    )
    assert response.status_code == 200
    assert (
        response.data["viewing_context"]["history"][-1]["listing_changes"][-1]["after"]
        == "12000"
    )


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"availability": "unavailable"}, "source_unavailable"),
        ({"capacity": 1}, "capacity_exceeded"),
        ({"archived": True}, "source_unavailable"),
    ],
)
def test_incompatible_accommodation_cancels_only_open_visit_with_explanation(
    rental_participants, change, reason
):
    _, _, _, prop, _ = rental_participants
    visit = request_visit(rental_participants)
    visit.stay_preferences = {"occupants": 2}
    visit.save(update_fields=["stay_preferences"])
    original = deepcopy(visit.offer_snapshot)
    edit_offer(prop, **change)
    visit.refresh_from_db()
    assert visit.status == "canceled" and visit.offer_snapshot == original
    assert visit.change_history[-1]["reason_code"] == reason


def test_unrelated_offer_and_editorial_changes_do_not_invalidate_visit(
    rental_participants,
):
    _, _, _, prop, _ = rental_participants
    visit = request_visit(rental_participants)
    other = deepcopy(prop.rental_inventory["offers"][0])
    other.update(id=str(uuid.uuid4()), name="Other accommodation")
    prop.rental_inventory["offers"].append(other)
    prop.save(update_fields=["rental_inventory"])
    inventory = deepcopy(prop.rental_inventory)
    inventory["revision"] += 1
    inventory["offers"][1]["availability"] = "unavailable"
    PropertyService.update_property(
        prop, {"rental_inventory": inventory, "title": "Edited name"}
    )
    visit.refresh_from_db()
    assert visit.status == "pending" and visit.revision == 1
    assert len(visit.change_history) == 1


def test_location_change_requires_a_new_viewing_and_preserves_old_identity(
    rental_participants,
):
    _, _, _, prop, _ = rental_participants
    visit = request_visit(rental_participants)
    PropertyService.update_property(prop, {"street": "Different physical address"})
    visit.refresh_from_db()
    assert visit.status == "canceled"
    assert visit.change_history[-1]["reason_code"] == "location_changed"


def test_visited_group_and_recorded_decisions_are_not_rewritten(rental_participants):
    from django.utils import timezone
    from core_apps.properties.models import PropertyVisitDecision

    owner, tenant, _, prop, _ = rental_participants
    _, process = reviewed_visit(rental_participants)
    visit = process.visit
    PropertyVisitDecision.objects.create(
        visit=visit,
        tenant=tenant,
        owner=owner,
        value="proceed",
        reason="",
        attested_at=timezone.now(),
        request_key=uuid.uuid4(),
        visit_revision=visit.revision,
        property_id_snapshot=prop.id,
        offer_id=visit.offer_id,
        offer_snapshot=visit.offer_snapshot,
    )
    original = {
        "status": visit.status,
        "revision": visit.revision,
        "change_history": deepcopy(visit.change_history),
    }
    edit_offer(prop, availability="unavailable")
    visit.refresh_from_db()
    assert visit.status == original["status"] and visit.revision == original["revision"]
    assert visit.change_history == original["change_history"]
    assert visit.participant_decisions.exists()


def test_group_loses_availability_with_one_consistent_process_history(
    rental_participants,
):
    _, _, _, prop, _ = rental_participants
    _, process = reviewed_visit(rental_participants)
    visit = process.visit
    edit_offer(prop, availability="unavailable")
    process.refresh_from_db()
    visit.refresh_from_db()
    assert process.status == "withdrawn" and process.consented_ids == []
    assert visit.status == "canceled"
    assert process.history[-1]["reason_code"] == "consent_or_source_changed"
    assert visit.change_history[-1]["reason_code"] == "source_unavailable"


def test_listing_price_does_not_reprice_accepted_negotiation(rental_participants):
    from core_apps.features.tests.test_negotiation_versions import create, decide
    from core_apps.features.services.negotiation_terms import current_selection

    _, tenant, _, prop, _ = rental_participants
    proposal, _, _ = create(rental_participants)
    assert decide(tenant, proposal).status_code == 200
    proposal.refresh_from_db()
    original = deepcopy(proposal.terms)
    edit_offer(prop, terms={"price": "12000", "price_period": "monthly"})
    proposal.refresh_from_db()
    assert proposal.status == "accepted" and proposal.terms == original
    assert current_selection(proposal)["terms"]["price"] == "12000"
    assert proposal.terms["monthly_rent"]["amount_minor"] == 850000


def test_different_bed_change_does_not_replace_the_visited_bed(rental_participants):
    from .test_visit_offer_snapshot import inventory_fixture

    _, _, _, prop, offer_id = rental_participants
    inventory_fixture(prop, offer_id)
    visit = request_visit(rental_participants)
    original = deepcopy(visit.offer_snapshot)
    inventory = deepcopy(prop.rental_inventory)
    inventory["revision"] += 1
    inventory["rooms"][0]["beds"].append(
        {"id": str(uuid.uuid4()), "name": "Another bed"}
    )
    PropertyService.update_property(prop, {"rental_inventory": inventory})
    visit.refresh_from_db()
    assert visit.revision == 1 and visit.status == "pending"
    assert visit.offer_snapshot == original
    # Replacing this bed, however, invalidates this exact visit.
    inventory["revision"] += 1
    inventory["offers"][0]["bed_id"] = inventory["rooms"][0]["beds"][1]["id"]
    PropertyService.update_property(prop, {"rental_inventory": inventory})
    visit.refresh_from_db()
    assert visit.status == "canceled" and visit.offer_snapshot == original
    assert visit.change_history[-1]["reason_code"] == "accommodation_changed"


def test_live_lease_amount_snapshot_document_and_status_survive_listing_edit(
    rental_participants,
):
    from datetime import timedelta
    from django.utils import timezone
    from core_apps.features.models import Lease
    from core_apps.features.tests.test_rental_phase2 import agreement_terms

    owner, tenant, _, prop, offer_id = rental_participants
    visit = request_visit(rental_participants)
    start = timezone.localdate()
    end = start + timedelta(days=60)
    terms = agreement_terms(start, end)
    lease = Lease.objects.create(
        property=prop,
        owner=owner,
        tenant=tenant,
        offer_id=offer_id,
        offer_snapshot=deepcopy(visit.offer_snapshot),
        template_id="eg-residential-v1",
        template_version="1",
        start_date=start,
        end_date=end,
        rent_amount_minor=1_000_000,
        status="active",
        legacy_read_only=False,
        terms=terms,
        policy_version="rental-policy-v1",
        document_id=uuid.uuid4(),
        document_hash="a" * 64,
    )
    original = {
        key: deepcopy(getattr(lease, key))
        for key in (
            "status",
            "terms",
            "offer_snapshot",
            "document_id",
            "document_hash",
            "rent_amount_minor",
            "revision",
        )
    }
    edit_offer(prop, terms={"price": "12000", "price_period": "monthly"})
    lease.refresh_from_db()
    assert {key: getattr(lease, key) for key in original} == original


@pytest.mark.django_db(transaction=True)
def test_membership_withdrawal_and_listing_change_share_lock_order(rental_participants):
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls
    from core_apps.features.tests.test_planning_cycles import group_action

    _, _, member, prop, _ = rental_participants
    state, process = reviewed_visit(rental_participants)
    parallel_calls(
        lambda i: (
            group_action(member, state, "leave")
            if i == 0
            else edit_offer(prop, availability="unavailable")
        )
    )
    process.refresh_from_db()
    process.visit.refresh_from_db()
    assert process.status == "withdrawn" and process.consented_ids == []
    assert process.visit.status == "canceled"


@pytest.mark.django_db(transaction=True)
def test_owner_accept_and_listing_unavailability_serialize(rental_participants):
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls
    from .test_viewing_response_commands import send

    owner, _, _, prop, _ = rental_participants
    visit = request_visit(rental_participants)
    result = parallel_calls(
        lambda i: (
            send(owner, visit, "accept")
            if i == 0
            else edit_offer(prop, availability="unavailable")
        )
    )
    assert result[0].status_code in {200, 409}
    visit.refresh_from_db()
    assert visit.status == "canceled"
    assert (
        len(
            [
                row
                for row in visit.change_history
                if row.get("reason_code") == "source_unavailable"
            ]
        )
        == 1
    )


@pytest.mark.django_db(transaction=True)
def test_attendance_committing_during_listing_edit_cannot_be_erased(
    rental_participants,
):
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls

    owner, tenant, _, prop, _ = rental_participants
    visit = request_visit(rental_participants)
    visit = command(
        owner, visit.id, {"expected_revision": visit.revision, "action": "accept"}
    )
    body = {
        "request_key": str(uuid.uuid4()),
        "expected_revision": visit.revision,
        "decision": "proceed",
        "attended": True,
    }
    result = parallel_calls(
        lambda i: (
            authenticated(tenant).post(
                f"/api/v1/properties/visits/{visit.id}/post-visit-decision/",
                body,
                format="json",
            )
            if i == 0
            else edit_offer(prop, availability="unavailable")
        )
    )
    visit.refresh_from_db()
    assert result[0].status_code in {200, 409}
    if result[0].status_code == 200:
        assert visit.participant_decisions.exists() and visit.status == "confirmed"
        assert not any(
            row.get("reason_code") == "source_unavailable"
            for row in visit.change_history
        )
    else:
        assert not visit.participant_decisions.exists() and visit.status == "canceled"
