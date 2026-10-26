"""Only affected independent allocations lose authority when their source changes."""

# flake8: noqa: F401,F811
from copy import deepcopy
import uuid
import pytest
from rest_framework.exceptions import NotFound
from core_apps.properties.models import Property
from core_apps.properties.services.property import PropertyService
from core_apps.properties.tests.test_viewing_listing_changes import edit_offer
from core_apps.features.services import group_booking_listing_changes as source
from core_apps.features.services.rental_lifecycle.group_bookings import booking_payload
from core_apps.features.services.rental_lifecycle.group_terms import notification_copy
from core_apps.features.services.negotiation_terms import current_selection
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.planning_models import PlanningEvent
from .test_group_booking_negotiation import setup, act, rental_participants, policy
from .test_cycle_concurrency import parallel_calls
from .test_rental_lifecycle import post

pytestmark = pytest.mark.django_db


def accepted(participants):
    item, body, _ = setup(participants)
    assert act(participants[0], item, "submit").status_code == 200
    assert act(participants[1], item, "terms/accept").status_code == 200
    return item, body


def change_beds(prop, index):
    prop.refresh_from_db()
    inventory = deepcopy(prop.rental_inventory)
    inventory["revision"] += 1
    inventory["rooms"][index]["beds"] = [
        {"id": str(uuid.uuid4()), "name": "Changed physical bed"}
    ]
    return PropertyService.update_property(prop, {"rental_inventory": inventory})


def republish(prop):
    Property.objects.filter(pk=prop.pk).update(status="verified", is_verified=True)


def test_exact_physical_change_blocks_only_affected_pending_consent(
    rental_participants, policy
):
    owner, rep, member, prop, _ = rental_participants
    item, body = accepted(rental_participants)
    original = deepcopy(item.participants.get(tenant=member).selection_snapshot)
    change_beds(prop, 1)
    item.refresh_from_db()
    own = booking_payload(item, member)
    assert "consent_group_booking" in own["available_actions"]
    assert "consent_group_booking" not in own["allowed_actions"]
    assert "withdraw_group_booking" in own["allowed_actions"]
    assert own["blocking_reasons"] == ["group_allocation_changed"]
    history = [r for r in own["history"] if r["action"] == source.ACTION]
    assert history[0]["allocations"][0]["tenant_id"] == str(member.id)
    assert (
        history[0]["allocations"][0]["listing_changes"][0]["field"] == "accommodation"
    )
    assert item.participants.get(tenant=member).selection_snapshot == original
    assert "consent_group_booking" in booking_payload(item, rep)["allowed_actions"]
    republish(prop)
    blocked = act(
        member, item, "consents", decision="accept", terms_digest=item.terms_digest
    )
    assert blocked.status_code == 409
    assert (
        act(
            rep, item, "consents", decision="accept", terms_digest=item.terms_digest
        ).status_code
        == 200
    )
    assert act(member, item, "withdraw").status_code == 200
    item.refresh_from_db()
    assert item.participants.get(tenant=rep).invitation_id
    assert not item.participants.get(tenant=member).invitation_id
    assert item.participants.get(tenant=member).consent_status == "withdrawn"


def test_existing_invitation_and_other_private_allocations_are_preserved(
    rental_participants, policy
):
    owner, rep, member, prop, _ = rental_participants
    item, _ = accepted(rental_participants)
    assert (
        act(
            rep, item, "consents", decision="accept", terms_digest=item.terms_digest
        ).status_code
        == 200
    )
    invitation = item.participants.get(tenant=rep).invitation
    original = deepcopy(invitation.offer_snapshot)
    change_beds(prop, 1)
    republish(prop)
    invitation.refresh_from_db()
    assert invitation.offer_snapshot == original and invitation.status == "pending"
    current_selection(invitation.terms_proposal)
    assert item.participants.get(tenant=member).invitation_id is None
    # Later physical changes to the already invited allocation must also be
    # rechecked by its individual phase; its preserved snapshot is not rewritten.
    change_beds(prop, 0)
    republish(prop)
    invitation.refresh_from_db()
    with pytest.raises(RentalConflict) as error:
        current_selection(invitation.terms_proposal)
    assert error.value.get_codes() == "accommodation_changed"
    assert invitation.offer_snapshot == original


def test_price_and_editorial_changes_keep_agreed_terms_and_consent(
    rental_participants, policy
):
    owner, rep, member, prop, _ = rental_participants
    item, _ = accepted(rental_participants)
    original = deepcopy(item.participants.get(tenant=rep).terms)
    edit_offer(
        prop,
        name="New public label",
        terms={"price": "15000", "price_period": "monthly"},
    )
    republish(prop)
    item.refresh_from_db()
    assert not source.events(item).exists()
    result = act(
        rep, item, "consents", decision="accept", terms_digest=item.terms_digest
    )
    assert result.status_code == 200, result.data
    row = item.participants.get(tenant=rep)
    assert row.terms == original and row.invitation.terms_proposal.terms == original


@pytest.mark.parametrize("edit", [{"street": "New physical address"}, {"floor": 8}])
def test_private_history_delivery_checks_current_membership_and_physical_location(
    rental_participants, policy, edit
):
    owner, rep, member, prop, _ = rental_participants
    item, _ = accepted(rental_participants)
    PropertyService.update_property(prop, edit)
    item.refresh_from_db()
    rows = booking_payload(item, member)["history"][-1]["allocations"]
    assert len(rows) == 1 and rows[0]["tenant_id"] == str(member.id)
    event = PlanningEvent.objects.get(
        recipient=member, destination__event_kind=source.ACTION
    )
    assert notification_copy(event)
    item.group.memberships.filter(user=member).update(status="left")
    with pytest.raises(NotFound):
        notification_copy(event)


def test_availability_resume_does_not_rewrite_deadline_or_private_terms(
    rental_participants, policy
):
    owner, rep, member, prop, _ = rental_participants
    item, _ = accepted(rental_participants)
    deadline = item.deadline
    original = deepcopy(item.participants.get(tenant=rep).terms)
    edit_offer(prop, availability="unavailable")
    item.refresh_from_db()
    assert booking_payload(item, rep)["blocking_reasons"] == [
        "group_allocation_unavailable"
    ]
    assert not source.invalidated(item)
    edit_offer(prop, availability="available")
    republish(prop)
    item.refresh_from_db()
    assert "consent_group_booking" in booking_payload(item, rep)["allowed_actions"]
    assert (
        item.deadline == deadline
        and item.participants.get(tenant=rep).terms == original
    )
    assert source.events(item).count() == 2


def test_material_change_cannot_revive_old_consent_and_owner_can_replace_before_invitations(
    rental_participants, policy
):
    owner, rep, member, prop, _ = rental_participants
    item, body = accepted(rental_participants)
    edit_offer(prop, capacity=2)
    edit_offer(prop, capacity=1)
    republish(prop)
    item.refresh_from_db()
    assert "consent_group_booking" not in booking_payload(item, rep)["allowed_actions"]
    assert (
        act(
            owner, item, "terms/withdraw", reason="Replace the affected accommodation"
        ).status_code
        == 200
    )
    # A fresh proposal needs the newly reviewed source; its history and consents
    # do not inherit the withdrawn agreement's authority.
    prop.refresh_from_db()
    body["request_key"] = str(uuid.uuid4())
    body["participants"][0]["offer_revision"] = prop.rental_inventory["offers"][0][
        "revision"
    ]
    result = post(owner, "group-booking-proposals/", body)
    assert result.status_code == 201, result.data
    assert result.data["resource"]["id"] != str(item.id)
    assert result.data["resource"]["status"] == "draft"
    assert not result.data["resource"]["blocking_reasons"]


@pytest.mark.django_db(transaction=True)
def test_concurrent_consent_and_physical_change_preserve_one_independent_result(
    rental_participants, policy
):
    owner, rep, member, prop, _ = rental_participants
    item, _ = accepted(rental_participants)

    def run(index):
        if index == 0:
            change_beds(prop, 1)
            return None
        return act(
            member, item, "consents", decision="accept", terms_digest=item.terms_digest
        ).status_code

    _, status = parallel_calls(run)
    assert status in {200, 409}
    item.refresh_from_db()
    row = item.participants.get(tenant=member)
    assert bool(row.invitation_id) == (status == 200)
    if row.invitation_id:
        republish(prop)
        with pytest.raises(RentalConflict):
            current_selection(row.invitation.terms_proposal)
    else:
        assert (
            "consent_group_booking"
            not in booking_payload(item, member)["allowed_actions"]
        )
