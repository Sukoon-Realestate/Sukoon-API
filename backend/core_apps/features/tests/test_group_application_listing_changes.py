"""A public-source change invalidates application consent before independent booking."""

# flake8: noqa: F401,F811
from copy import deepcopy
import pytest
from .test_rental_phase2 import rental_participants, authenticated
from .test_planning_cycles import (
    create_group,
    join_group,
    API,
    configured_planning_offer,
)
from .test_funded_settlement import command
from .test_cycle_concurrency import parallel_calls
from .test_rental_lifecycle import policy
from .test_group_booking_negotiation import setup as negotiated_setup, act
from core_apps.properties.models import Property
from core_apps.properties.tests.test_viewing_listing_changes import edit_offer
from core_apps.properties.services.property import PropertyService
from core_apps.features.planning_models import GroupProcess, HousingGroup, PlanningEvent
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from core_apps.features.services.planning import selection_payload
from core_apps.features.services.group_process_events import authorize

pytestmark = pytest.mark.django_db


def application(parties):
    _, tenant, member, prop, offer_id = parties
    state = create_group(tenant, prop)
    state, _, _ = join_group(tenant, member, state)
    group = HousingGroup.objects.get(id=state["id"])
    people = [str(tenant.id), str(member.id)]
    selected = selection_payload(resolve_offer_snapshot(prop, offer_id, 2)[1])
    return GroupProcess.objects.create(
        group=group,
        initiated_by=tenant,
        property=prop,
        kind="application",
        roster_revision=group.roster_revision,
        access_group_revision=group.revision,
        status="under_review",
        selection=selected,
        participant_ids=people,
        consented_ids=people,
    )


def test_changed_price_withdraws_old_application_keeps_consents_in_private_audit(
    rental_participants,
):
    owner, tenant, member, prop, _ = rental_participants
    item = application(rental_participants)
    original = deepcopy(item.selection)
    prop = edit_offer(
        prop, terms={**prop.rental_inventory["offers"][0]["terms"], "price": "12000"}
    )
    item.refresh_from_db()
    assert item.status == "withdrawn" and item.revision == 2
    assert item.consented_ids == [] and item.selection == original
    assert set(item.history[0]["previous_consented_ids"]) == {
        str(tenant.id),
        str(member.id),
    }
    response = authenticated(owner).get(API + f"group-applications/{item.id}/")
    assert response.status_code == 200, response.data
    assert response.data["history"][0]["listing_changes"] == [
        {"field": "price", "before": "10000", "after": "12000"}
    ]
    assert "previous_consented_ids" not in str(response.data)
    events = list(
        PlanningEvent.objects.filter(destination__event_kind="group_process_changed")
    )
    assert {row.recipient_id for row in events} == {owner.pk, tenant.pk, member.pk}
    assert all(authorize(row) for row in events)
    PropertyService.update_property(prop, {"title": "New title"})
    item.refresh_from_db()
    assert item.revision == 2 and len(item.history) == 1


def test_editorial_changes_preserve_group_approval(rental_participants):
    _, _, _, prop, _ = rental_participants
    item = application(rental_participants)
    PropertyService.update_property(prop, {"title": "New title"})
    item.refresh_from_db()
    assert item.status == "under_review" and item.revision == 1 and item.history == []


def test_accepted_independent_private_terms_survive_public_price_edit(
    rental_participants, policy
):
    owner, representative, _, prop, _ = rental_participants
    proposal, _, _ = negotiated_setup(rental_participants)
    assert act(owner, proposal, "submit").status_code == 200
    assert act(representative, proposal, "terms/accept").status_code == 200
    application = proposal.application
    application.selection = selection_payload(
        resolve_offer_snapshot(prop, prop.rental_inventory["offers"][0]["id"], 1)[1]
    )
    application.save(update_fields=["selection"])
    old = deepcopy(proposal.participants.first().terms)
    edit_offer(
        prop, terms={**prop.rental_inventory["offers"][0]["terms"], "price": "12000"}
    )
    proposal.refresh_from_db()
    application.refresh_from_db()
    assert proposal.status == "awaiting_participants"
    assert application.status == "approved_to_proceed" and not application.history
    assert proposal.participants.first().terms == old


@pytest.mark.django_db(transaction=True)
def test_owner_approval_and_listing_change_do_not_deadlock_or_leave_stale_approval(
    rental_participants,
):
    owner, _, _, prop, _ = rental_participants
    item = application(rental_participants)

    def run(index):
        if index == 0:
            edit_offer(Property.objects.get(pk=prop.pk), availability="unavailable")
            return None
        return authenticated(owner).post(
            API + f"group-applications/{item.id}/approve/",
            command(item.revision, action="approve"),
            format="json",
        )

    _, response = parallel_calls(run)
    assert response.status_code in (200, 403, 409), response.data
    item.refresh_from_db()
    assert item.status == "withdrawn" and item.consented_ids == []
