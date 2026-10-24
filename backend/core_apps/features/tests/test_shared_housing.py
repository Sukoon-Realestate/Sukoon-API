import copy
import uuid
from datetime import timedelta
from unittest.mock import patch
import pytest
from django.utils import timezone
from core_apps.features.planning_models import RoommateConnection, PlanningEvent
from core_apps.features.shared_housing_models import (
    SharedHousingPlan,
    SharedHousingAllocation,
)
from core_apps.features.models import RentalInterest, TenancyInvitation
from .test_rental_phase2 import (
    rental_participants,
    authenticated,
    agreement_terms,
    complete_owner_onboarding,
)
from .test_funded_settlement import command

API = "/api/v1/features/v1/"
pytestmark = pytest.mark.django_db


@pytest.fixture
def pair(rental_participants, settings):
    settings.SHARED_HOUSING_ENABLED = True
    owner, first, second, prop, _ = rental_participants
    rooms, offers = [], []
    for i in range(2):
        room, offer = str(uuid.uuid4()), str(uuid.uuid4())
        rooms.append({"id": room, "name": f"Room {i + 1}", "capacity": 1, "beds": []})
        offers.append(
            {
                "id": offer,
                "revision": 1,
                "rental_scope": "room",
                "room_ids": [room],
                "name": f"Room {i + 1}",
                "availability": "available",
                "archived": False,
                "capacity": 1,
                "terms": {
                    "price": "10000",
                    "price_period": "monthly",
                    "deposit": "10000",
                    "rental_period": 1,
                    "suitable_for": "all",
                    "description": "Room",
                    "rules": [],
                    "smoking_allowed": False,
                },
            }
        )
    prop.rental_inventory = {
        "schema_version": 1,
        "revision": 1,
        "mode": "partial",
        "rooms": rooms,
        "offers": offers,
    }
    prop.save()
    ordered = sorted([first, second], key=lambda value: value.pk)
    connection = RoommateConnection.objects.create(
        first=ordered[0], second=ordered[1], requester=first, status="accepted"
    )
    return owner, first, second, prop, connection


def post(user, path, data, status=200):
    response = authenticated(user).post(API + path, data, format="json")
    assert response.status_code == status, response.data
    return response.data.get("resource", response.data)


def create(pair):
    _, first, second, prop, connection = pair
    body = command(
        connection_id=str(connection.id),
        criteria={
            "city_id": str(prop.city.id),
            "start_on": str(timezone.localdate() + timedelta(days=10)),
            "months": 2,
            "budgets": {str(first.id): 1200000, str(second.id): 1200000},
        },
    )
    return post(first, "shared-housing-plans/", body, 201), body


def act(user, plan, action, **data):
    return post(
        user,
        f"shared-housing-plans/{plan['id']}/{action}/",
        command(plan["revision"], **data),
    )


def proposal_act(user, plan, action, **data):
    identifier = plan["proposals"][0]["id"]
    return post(
        user,
        f"shared-housing-plans/{plan['id']}/proposals/{identifier}/{action}/",
        command(plan["revision"], **data),
    )


def candidate(pair):
    _, first, second, prop, _ = pair
    plan, _ = create(pair)
    plan = act(second, plan, "accept_invite")
    lines = [
        {
            "tenant_id": str(user.id),
            "selection": {
                "property_id": str(prop.id),
                "offer_id": offer["id"],
                "offer_revision": 1,
            },
        }
        for user, offer in zip([first, second], prop.rental_inventory["offers"])
    ]
    plan = post(
        first,
        f"shared-housing-plans/{plan['id']}/proposals/",
        command(plan["revision"], allocations=lines),
    )
    return plan


def submitted(pair):
    _, first, second, _, _ = pair
    plan = candidate(pair)
    plan = proposal_act(first, plan, "consent_selection", consent=True)
    plan = proposal_act(second, plan, "consent_selection", consent=True)
    return proposal_act(first, plan, "submit")


def accepted(pair):
    owner, _, _, _, _ = pair
    plan = submitted(pair)
    complete_owner_onboarding(owner)
    from datetime import date

    terms = agreement_terms(
        date.fromisoformat(plan["criteria"]["start_on"]),
        date.fromisoformat(plan["criteria"]["end_on"]),
    )
    return proposal_act(
        owner,
        plan,
        "owner_accept",
        allocation_terms=[
            {"tenant_id": row["id"], "terms": terms} for row in plan["participants"]
        ],
    )


def test_pair_create_replay_and_crossed_creation(pair):
    _, first, second, _, connection = pair
    plan, body = create(pair)
    assert post(first, "shared-housing-plans/", body, 201)["id"] == plan["id"]
    other = {**body, "request_key": str(uuid.uuid4())}
    assert post(second, "shared-housing-plans/", other, 201)["id"] == plan["id"]
    assert SharedHousingPlan.objects.count() == 1
    assert PlanningEvent.objects.filter(
        recipient=second, destination__action_type="open_shared_housing_plan"
    ).exists()


def test_publication_needs_two_consents_and_reapproval_after_edit(pair):
    owner, first, second, _, _ = pair
    plan, _ = create(pair)
    plan = act(second, plan, "accept_invite")
    post(
        first,
        f"shared-housing-plans/{plan['id']}/publish/",
        command(plan["revision"]),
        409,
    )
    for user in [first, second]:
        plan = act(user, plan, "approve_publication", consent=True)
    plan = act(first, plan, "publish")
    assert authenticated(owner).get(API + "shared-housing-demand/").data["count"] == 1
    plan = act(first, plan, "edit", criteria=plan["criteria"])
    assert not plan["published"] and not plan["publication_consents"]


def test_no_single_person_submit_or_owner_partial_decision(pair):
    owner, first, _, _, _ = pair
    plan = candidate(pair)
    plan = proposal_act(first, plan, "consent_selection", consent=True)
    path = f"shared-housing-plans/{plan['id']}/proposals/{plan['proposals'][0]['id']}"
    post(first, path + "/submit/", command(plan["revision"]), 409)
    post(owner, path + "/owner_accept/", command(plan["revision"]), 403)
    assert RentalInterest.objects.count() == 0


def test_overlap_is_rejected(pair):
    _, first, second, _, _ = pair
    plan = candidate(pair)
    lines = plan["proposals"][0]["allocations"]
    lines[1]["selection"] = copy.deepcopy(lines[0]["selection"])
    post(
        first,
        f"shared-housing-plans/{plan['id']}/proposals/",
        command(plan["revision"], allocations=lines),
        409,
    )


def test_legacy_individual_mutation_cannot_escape_joint_review(pair):
    owner, first, _, _, _ = pair
    plan = submitted(pair)
    row = SharedHousingAllocation.objects.filter(tenant=first).get()
    post(
        first,
        f"rental-interests/{row.interest.id}/respond/",
        command(row.interest.revision, decision="withdraw"),
        409,
    )
    assert len(plan["proposals"][0]["allocations"]) == 2


def test_submission_rolls_back_both_interests_on_second_failure(pair):
    _, first, second, _, _ = pair
    plan = candidate(pair)
    plan = proposal_act(first, plan, "consent_selection", consent=True)
    plan = proposal_act(second, plan, "consent_selection", consent=True)
    from core_apps.features.services.rental_application_records import create_interest

    calls = []

    def fail_second(**kwargs):
        calls.append(1)
        if len(calls) == 2:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Injected second failure")
        return create_interest(**kwargs)

    with patch(
        "core_apps.features.services.shared_housing.commands.create_interest",
        side_effect=fail_second,
    ):
        post(
            first,
            f"shared-housing-plans/{plan['id']}/proposals/{plan['proposals'][0]['id']}/submit/",
            command(plan["revision"]),
            400,
        )
    assert RentalInterest.objects.count() == 0


def test_complete_joint_review_hands_off_two_private_independent_invitations(pair):
    owner, first, second, _, _ = pair
    plan = accepted(pair)
    plan = proposal_act(first, plan, "consent_terms", independent_consent=True)
    path = f"shared-housing-plans/{plan['id']}/proposals/{plan['proposals'][0]['id']}/send_invitations/"
    post(owner, path, command(plan["revision"]), 409)
    plan = proposal_act(second, plan, "consent_terms", independent_consent=True)
    body = command(plan["revision"])
    plan = post(owner, path, body)
    assert post(owner, path, body)["id"] == plan["id"]
    assert TenancyInvitation.objects.count() == 2
    assert plan["status"] == "handed_off"
    private = authenticated(first).get(API + f"shared-housing-plans/{plan['id']}/").data
    other = next(
        row
        for row in private["proposals"][0]["allocations"]
        if row["tenant_id"] == str(second.id)
    )
    assert other["invitation_id"] == other["lease_id"] == other["interest_id"] == ""
    assert other["terms"] == {}
    # Leaving the social connection never revokes the other person's invitation.
    post(
        first,
        f"roommate-connections/{pair[4].id}/withdraw/",
        command(pair[4].revision, decision="withdraw"),
    )
    assert TenancyInvitation.objects.filter(status="pending").count() == 2


def test_withdraw_closes_both_before_handoff(pair):
    _, first, second, _, _ = pair
    plan = submitted(pair)
    plan = act(second, plan, "withdraw")
    assert plan["status"] == "closed"
    assert RentalInterest.objects.filter(status="withdrawn").count() == 2


def test_capability_disabled_blocks_create_but_keeps_history(pair, settings):
    _, first, _, _, _ = pair
    plan, body = create(pair)
    settings.SHARED_HOUSING_ENABLED = False
    body["request_key"] = str(uuid.uuid4())
    post(first, "shared-housing-plans/", body, 403)
    assert (
        authenticated(first)
        .get(API + f"shared-housing-plans/{plan['id']}/")
        .status_code
        == 200
    )


def test_owner_cannot_read_private_unpublished_plan(pair):
    owner, _, _, _, _ = pair
    plan, _ = create(pair)
    assert (
        authenticated(owner)
        .get(API + f"shared-housing-plans/{plan['id']}/")
        .status_code
        == 404
    )
