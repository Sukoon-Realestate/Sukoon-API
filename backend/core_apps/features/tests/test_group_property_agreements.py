"""Private listing terms match the student's allocation before/after follow-up."""

# flake8: noqa: F401, F811
import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from .test_rental_phase2 import rental_participants, authenticated
from .test_rental_lifecycle import policy, PREFIX
from .test_group_booking_negotiation import setup, act

pytestmark = pytest.mark.django_db


def listing(user, prop, offer, **extra):
    return authenticated(user).get(
        PREFIX + "group-booking-proposals/",
        {
            "property_id": str(prop.id),
            "offer_id": offer,
            "active_agreements": True,
            **extra,
        },
    )


def accepted(participants):
    owner, rep, *_ = participants
    item, _, _ = setup(participants)
    assert act(owner, item, "submit").status_code == 200
    assert act(rep, item, "terms/accept").status_code == 200
    item.refresh_from_db()
    return item


def test_listing_only_shows_viewers_exact_allocation(rental_participants, policy):
    owner, rep, member, prop, _ = rental_participants
    item = accepted(rental_participants)
    mine, theirs = item.participants.get(tenant=rep), item.participants.get(
        tenant=member
    )
    response = listing(rep, prop, mine.offer_id)
    assert response.status_code == 200, response.data
    assert response["Cache-Control"] == "private, no-store"
    assert [row["id"] for row in response.data["results"]] == [str(item.id)]
    assert listing(rep, prop, theirs.offer_id).data["results"] == []
    assert listing(member, prop, mine.offer_id).data["results"] == []
    assert listing(owner, prop, mine.offer_id).data["results"] == []
    assert (
        listing(rep, prop, mine.offer_id, academic_plan_id=str(uuid.uuid4())).data[
            "results"
        ]
        == []
    )
    assert (
        authenticated(rep)
        .get(PREFIX + "group-booking-proposals/", {"active_agreements": True})
        .status_code
        == 400
    )
    detail = authenticated(rep).get(PREFIX + f"group-booking-proposals/{item.id}/")
    assert detail["Cache-Control"] == "private, no-store"


def test_expired_or_changed_roster_is_not_offered_as_current_agreement(
    rental_participants, policy
):
    _, rep, _, prop, _ = rental_participants
    item = accepted(rental_participants)
    mine = item.participants.get(tenant=rep)
    item.group.roster_revision += 1
    item.group.save(update_fields=["roster_revision"])
    assert listing(rep, prop, mine.offer_id).data["results"] == []
    item.group.roster_revision -= 1
    item.group.save(update_fields=["roster_revision"])
    item.deadline = timezone.now() - timedelta(seconds=1)
    item.save(update_fields=["deadline"])
    assert listing(rep, prop, mine.offer_id).data["results"] == []


def test_started_student_followup_moves_to_same_private_terms_projection(
    rental_participants, policy
):
    _, rep, member, prop, _ = rental_participants
    item = accepted(rental_participants)
    mine = item.participants.get(tenant=rep)
    assert (
        act(
            rep, item, "consents", decision="accept", terms_digest=item.terms_digest
        ).status_code
        == 200
    )
    mine.refresh_from_db()
    assert listing(rep, prop, mine.offer_id).data["results"] == []
    query = {
        "property_id": str(prop.id),
        "offer_id": mine.offer_id,
        "active_agreements": True,
    }
    response = authenticated(rep).get(
        PREFIX + "terms-proposals/", {**query, "workspace": "student"}
    )
    assert response.status_code == 200, response.data
    assert [row["id"] for row in response.data["results"]] == [
        str(mine.invitation.terms_proposal.id)
    ]
    assert response.data["results"][0]["terms"] == mine.terms
    assert (
        authenticated(rep)
        .get(PREFIX + "terms-proposals/", {**query, "workspace": "individual"})
        .data["results"]
        == []
    )
    assert (
        authenticated(member)
        .get(PREFIX + "terms-proposals/", {**query, "workspace": "student"})
        .data["results"]
        == []
    )
