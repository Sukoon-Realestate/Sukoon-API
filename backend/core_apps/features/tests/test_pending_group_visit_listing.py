"""Attendance survives price edits; physical changes require a new review."""

# flake8: noqa: F401,F811
from copy import deepcopy
import pytest
from .test_rental_phase2 import rental_participants, authenticated
from .test_planning_cycles import (
    create_group,
    join_group,
    configured_planning_offer,
    API,
)
from .test_group_process_history import consent
from .test_funded_settlement import command
from .test_cycle_concurrency import parallel_calls
from core_apps.features.planning_models import GroupProcess, PlanningEvent
from core_apps.features.services.planning import selection_payload
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from core_apps.properties.models import Property
from core_apps.properties.tests.test_viewing_listing_changes import edit_offer

pytestmark = pytest.mark.django_db


def pending(parties):
    _, tenant, member, prop, offer_id = parties
    state = create_group(tenant, prop)
    state, _, _ = join_group(tenant, member, state)
    selected = selection_payload(resolve_offer_snapshot(prop, offer_id, 2)[1])
    state = consent(
        tenant,
        state,
        "request_visit",
        selection=selected,
        participant_ids=[str(tenant.id), str(member.id)],
    )
    return state, GroupProcess.objects.get(id=state["visits"][0]["id"])


def approve(member, state, item):
    return authenticated(member).post(
        API + f"housing-groups/{state['id']}/consent_visit/",
        command(
            state["revision"],
            roster_revision=state["roster_revision"],
            action="consent_visit",
            consent=True,
            item_id=str(item.id),
            item_revision=item.revision,
        ),
        format="json",
    )


def test_price_change_keeps_attendance_and_current_version_is_required(
    rental_participants,
):
    owner, tenant, member, prop, _ = rental_participants
    state, item = pending(rental_participants)
    original = deepcopy(item.selection)
    prop = edit_offer(
        prop, terms={**prop.rental_inventory["offers"][0]["terms"], "price": "12000"}
    )
    assert approve(member, state, item).status_code == 409
    item.refresh_from_db()
    assert item.status == "collecting_consent" and item.visit_id is None
    assert item.consented_ids == [str(tenant.id)]
    assert item.selection["terms"]["price"] == "12000"
    assert item.history[0]["previous_selection"] == original
    assert item.history[0]["listing_changes"] == [
        {"field": "price", "before": "10000", "after": "12000"}
    ]
    result = authenticated(member).get(API + f"housing-groups/{state['id']}/")
    assert "previous_selection" not in str(result.data)
    events = PlanningEvent.objects.filter(
        destination__event_kind="group_process_changed"
    )
    assert set(events.values_list("recipient_id", flat=True)) == {tenant.pk, member.pk}
    assert (
        approve(member, state, item).status_code == 404
    )  # Still awaiting property review.
    # Isolate the already-covered moderation cycle, then exercise real dispatch.
    Property.objects.filter(pk=prop.pk).update(status="verified", is_verified=True)
    response = approve(member, state, item)
    assert response.status_code == 200, response.data
    item.refresh_from_db()
    assert (
        item.status == "submitted"
        and item.visit.offer_snapshot["terms"]["price"] == "12000"
    )
    assert set(item.consented_ids) == {str(tenant.id), str(member.id)}


@pytest.mark.parametrize("change", [{"availability": "unavailable"}, {"capacity": 1}])
def test_physical_change_withdraws_pending_attendance(rental_participants, change):
    _, _, member, prop, _ = rental_participants
    state, item = pending(rental_participants)
    edit_offer(prop, **change)
    item.refresh_from_db()
    assert item.status == "withdrawn" and item.consented_ids == [] and not item.visit_id
    assert approve(member, state, item).status_code == 403


@pytest.mark.django_db(transaction=True)
def test_price_edit_and_final_consent_keep_one_process_and_current_evidence(
    rental_participants,
):
    _, _, member, prop, _ = rental_participants
    state, item = pending(rental_participants)

    def run(index):
        if index == 0:
            current = Property.objects.get(pk=prop.pk)
            edit_offer(
                current,
                terms={
                    **current.rental_inventory["offers"][0]["terms"],
                    "price": "12000",
                },
            )
            return None
        return approve(member, state, item)

    _, response = parallel_calls(run)
    assert response.status_code in (200, 409), response.data
    item.refresh_from_db()
    if item.visit_id:
        assert item.visit.status == "pending"
        assert item.visit.change_history[-1]["reason_code"] == "terms_changed"
    else:
        assert (
            item.status == "collecting_consent"
            and item.selection["terms"]["price"] == "12000"
        )
        assert len(item.history) == 1


def test_offer_label_refresh_does_not_invalidate_attendance(rental_participants):
    _, tenant, member, prop, _ = rental_participants
    state, item = pending(rental_participants)
    edit_offer(prop, name="Updated room label")
    item.refresh_from_db()
    assert item.consented_ids == [str(tenant.id)] and not item.history
    assert item.selection["name"] == "Updated room label"
    assert not PlanningEvent.objects.filter(
        destination__event_kind="group_process_changed"
    ).exists()
    Property.objects.filter(pk=prop.pk).update(status="verified", is_verified=True)
    assert approve(member, state, item).status_code == 200
