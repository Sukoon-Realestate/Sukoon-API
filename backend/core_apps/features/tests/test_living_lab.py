"""Synthetic pilot tests. No provider, payment, or deployment claims."""

import copy
from datetime import timedelta
import uuid

import pytest
from django.utils import timezone

from core_apps.features.living_lab_models import LivingLabRun, SharedArrangementSnapshot
from core_apps.features.models import (
    GroupMembership,
    HousingGroup,
    IdempotencyRecord,
    Lease,
)
from core_apps.features.services.planning import selection_payload
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from . import test_rental_phase2 as rental_fixtures
from .test_rental_phase2 import authenticated

rental_participants = rental_fixtures.rental_participants

API = "/api/v1/features/v1/"


@pytest.fixture(autouse=True)
def lab_capability(settings):
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = ["shared_living_lab"]
    settings.PLANNING_ENABLED_SERVICES = ["housing_groups"]
    settings.LIVING_LAB_MAX_RUNS_PER_LAB = 3
    settings.LIVING_LAB_MAX_RUNS_PER_GROUP_DAY = 6


def command(revision=0, **values):
    return {"request_key": str(uuid.uuid4()), "expected_revision": revision, **values}


def post(user, path, data, expected=200):
    response = authenticated(user).post(API + path, data, format="json")
    assert response.status_code == expected, response.data
    if expected < 400:
        assert set(response.json()) == {"message", "data"}
        assert response["Cache-Control"] == "private, no-store"
    return response


@pytest.fixture
def context(rental_participants):
    owner, admin, member, prop, offer_id = rental_participants
    rooms = [
        {"id": str(uuid.uuid4()), "name": "Quiet room", "capacity": 2, "beds": []},
        {"id": str(uuid.uuid4()), "name": "Second room", "capacity": 1, "beds": []},
    ]
    prop.rental_inventory["rooms"] = rooms
    prop.rental_inventory["offers"][0]["terms"] = {
        "price": "100.01",
        "price_period": "monthly",
        "deposit": "50.01",
    }
    prop.save()
    _, selected = resolve_offer_snapshot(prop, offer_id, 2)
    group = HousingGroup.objects.create(name="Voluntary group", capacity=2)
    GroupMembership.objects.create(group=group, user=admin, role="admin")
    GroupMembership.objects.create(group=group, user=member, role="member")
    shortlist = {
        "id": str(uuid.uuid4()),
        "revision": 1,
        "selection": selection_payload(selected),
        "comments": [],
        "voter_ids": [],
    }
    group.shortlist = [shortlist]
    group.save()
    return owner, admin, member, prop, group, rooms


def create_lab(context):
    _, admin, _, _, group, _ = context
    start = timezone.localdate() + timedelta(days=10)
    return post(
        admin,
        f"housing-groups/{group.id}/living-labs/",
        command(
            expected_group_revision=group.revision,
            shortlist_id=group.shortlist[0]["id"],
            title="Shared home",
            starts_on=str(start),
            ends_on_exclusive=str(start + timedelta(days=90)),
            house_rules=["Discuss quiet hours together."],
        ),
        201,
    ).data["resource"]


def read(user, lab):
    response = authenticated(user).get(API + f"living-labs/{lab['id']}/")
    assert response.status_code == 200, response.data
    return response.data


def requirements(user, lab, **overrides):
    values = {
        "rent_max_minor": 123456789,
        "deposit_max_minor": 543210,
        "accepted_start_on": lab["starts_on"],
        "accepted_end_on": lab["ends_on_exclusive"],
        "private_room": False,
        "required_room_id": "",
        "preferred_room_id": "",
    }
    values.update(overrides)
    return post(
        user,
        f"living-labs/{lab['id']}/my-requirements/",
        command(
            lab["revision"],
            status="provided",
            purpose_version="living-lab-private-v1",
            purpose_accepted=True,
            values=values,
        ),
    ).data["resource"]


def ready(context):
    _, admin, member, _, _, _ = context
    lab = create_lab(context)
    lab = requirements(admin, lab)
    lab = requirements(member, lab)
    return post(admin, f"living-labs/{lab['id']}/runs/", command(lab["revision"])).data[
        "resource"
    ]


def respond(user, lab, decision="accept"):
    run = lab["latest_run"]
    return post(
        user,
        f"living-labs/{lab['id']}/responses/",
        command(
            lab["revision"],
            run_id=run["id"],
            candidate_id=run["candidates"][0]["id"],
            input_revision=lab["input_revision"],
            decision=decision,
        ),
    ).data["resource"]


@pytest.mark.django_db
def test_private_inputs_are_explicit_own_only_and_never_in_shared_or_receipt_dtos(
    context,
):
    owner, admin, member, _, _, _ = context
    lab = create_lab(context)
    path = f"living-labs/{lab['id']}/my-requirements/"
    post(
        admin,
        path,
        command(lab["revision"], status="provided", purpose_accepted=False, values={}),
        400,
    )
    post(
        admin,
        path,
        command(lab["revision"], user_id=str(member.id), status="omitted"),
        400,
    )
    lab = requirements(admin, lab)
    mine = authenticated(admin).get(API + path).data
    theirs = authenticated(member).get(API + path).data
    assert mine["values"]["rent_max_minor"] == 123456789
    assert theirs["status"] == "omitted" and theirs["values"] == {}
    assert authenticated(owner).get(API + path).status_code == 404
    assert "123456789" not in str(read(member, lab))
    assert "123456789" not in str(
        list(IdempotencyRecord.objects.values_list("response_data", flat=True))
    )
    invalid = post(
        admin, f"living-labs/{lab['id']}/runs/", command(lab["revision"])
    ).data["resource"]
    assert invalid["latest_run"]["outcome"] == "invalid_input"
    assert invalid["latest_run"]["candidates"] == []


@pytest.mark.django_db
def test_exact_remainder_private_bounds_and_agreement_is_planning_then_unapproved_canonical_handoff(
    context,
):
    _, admin, member, _, group, _ = context
    lab = ready(context)
    run = lab["latest_run"]
    assert run["outcome"] == "feasible"
    assert 1 <= len(run["candidates"]) <= 3
    for candidate in run["candidates"]:
        shares = candidate["shares"]
        assert sum(row["rent_minor"] for row in shares) == 10001
        assert sum(row["deposit_minor"] for row in shares) == 5001
        assert shares[0]["user_id"] < shares[1]["user_id"]
        assert shares[0]["rent_minor"] == 5001 and shares[1]["rent_minor"] == 5000
        assert all(row["room_name"] for row in shares)
        assert candidate["price_period"] == "monthly"
        assert candidate["inventory_reserved"] is False
    lab = respond(admin, lab)
    assert lab["status"] == "collecting_responses" and lab["agreements"] == []
    lab = respond(member, lab)
    assert lab["status"] == "agreed" and len(lab["agreements"]) == 1
    assert Lease.objects.count() == 0
    current = read(admin, lab)
    handed = post(
        admin,
        f"living-labs/{lab['id']}/prepare-cost-proposal/",
        command(
            current["revision"],
            expected_group_revision=current["group_revision"],
            agreement_id=current["agreements"][0]["id"],
        ),
    ).data["resource"]
    group.refresh_from_db()
    assert handed["handoff_proposal_id"] == group.proposals[0]["id"]
    assert group.proposals[0]["approved_by"] == []
    assert sum(group.proposals[0]["contributions"].values()) == 10001
    assert Lease.objects.count() == 0


@pytest.mark.django_db
def test_hard_budget_and_room_conflicts_remain_coarse_without_silent_relaxation(
    context,
):
    _, admin, member, _, _, rooms = context
    lab = create_lab(context)
    lab = requirements(admin, lab, required_room_id=rooms[0]["id"], private_room=True)
    lab = requirements(member, lab, required_room_id=rooms[0]["id"])
    lab = post(admin, f"living-labs/{lab['id']}/runs/", command(lab["revision"])).data[
        "resource"
    ]
    assert lab["latest_run"]["outcome"] == "infeasible"
    assert lab["latest_run"]["explanation_code"] == "no_workable_arrangement"
    lab = requirements(admin, lab, rent_max_minor=1)
    lab = post(admin, f"living-labs/{lab['id']}/runs/", command(lab["revision"])).data[
        "resource"
    ]
    assert lab["latest_run"]["outcome"] == "infeasible"
    assert "rent_max_minor" not in str(lab["latest_run"])


@pytest.mark.django_db
def test_changed_requirements_stale_acceptance_and_quote_changes_revoke_handoff(
    context,
):
    _, admin, member, prop, _, _ = context
    lab = ready(context)
    previous = copy.deepcopy(lab)
    lab = respond(admin, lab)
    lab = requirements(member, lab)
    old = previous["latest_run"]
    post(
        member,
        f"living-labs/{lab['id']}/responses/",
        command(
            lab["revision"],
            run_id=old["id"],
            candidate_id=old["candidates"][0]["id"],
            input_revision=previous["input_revision"],
            decision="accept",
        ),
        403,
    )
    assert SharedArrangementSnapshot.objects.count() == 0
    lab = post(admin, f"living-labs/{lab['id']}/runs/", command(lab["revision"])).data[
        "resource"
    ]
    lab = respond(admin, lab)
    lab = respond(member, lab)
    immutable = copy.deepcopy(lab["agreements"][0]["snapshot"])
    prop.rental_inventory["rooms"][0]["name"] = "Later renamed room"
    prop.rental_inventory["offers"][0]["terms"]["price"] = "200.00"
    prop.rental_inventory["offers"][0]["revision"] += 1
    prop.save()
    changed = read(admin, lab)
    assert changed["status"] == "needs_revision"
    assert changed["latest_run"]["outcome"] == "stale"
    assert "prepare_cost_proposal" not in changed["allowed_actions"]
    post(
        admin,
        f"living-labs/{lab['id']}/prepare-cost-proposal/",
        command(
            lab["revision"],
            expected_group_revision=lab["group_revision"],
            agreement_id=lab["agreements"][0]["id"],
        ),
        409,
    )
    assert SharedArrangementSnapshot.objects.get().snapshot == immutable


@pytest.mark.django_db
def test_replay_conflicts_probing_limits_and_rejoin_cannot_restore_old_receipts(
    context,
):
    _, admin, member, _, group, _ = context
    lab = create_lab(context)
    lab = requirements(admin, lab)
    lab = requirements(member, lab)
    body = command(lab["revision"])
    path = f"living-labs/{lab['id']}/runs/"
    first = post(admin, path, body)
    assert post(admin, path, body).data == first.data
    assert LivingLabRun.objects.count() == 1
    post(admin, path, {**body, "arbitrary_price": 1}, 409)
    lab = first.data["resource"]
    for _ in range(2):
        lab = requirements(admin, lab)
        lab = post(admin, path, command(lab["revision"])).data["resource"]
    lab = requirements(admin, lab)
    post(admin, path, command(lab["revision"]), 409)
    row = GroupMembership.objects.get(group=group, user=member)
    row.status = "left"
    row.save()
    assert (
        authenticated(member).get(API + f"living-labs/{lab['id']}/").status_code == 404
    )
    group.revision += 2
    group.roster_revision += 2
    group.save()
    row.status, row.joined_revision = "active", group.revision
    row.save()
    assert (
        authenticated(member)
        .get(API + f"living-labs/{lab['id']}/my-requirements/")
        .status_code
        == 404
    )
    assert (
        authenticated(member)
        .get(API + f"housing-groups/{group.id}/living-labs/")
        .data["results"]
        == []
    )
    assert read(admin, lab)["status"] == "needs_revision"


@pytest.mark.django_db
def test_disabled_feature_keeps_history_and_private_withdrawal_does_not_rewrite_agreements(
    context, settings
):
    _, admin, member, _, _, _ = context
    lab = ready(context)
    lab = respond(admin, lab)
    lab = respond(member, lab)
    snapshot = copy.deepcopy(lab["agreements"][0]["snapshot"])
    lab = post(
        member, f"living-labs/{lab['id']}/withdraw/", command(lab["revision"])
    ).data["resource"]
    assert lab["status"] == "needs_revision"
    assert (
        authenticated(member)
        .get(API + f"living-labs/{lab['id']}/my-requirements/")
        .data["values"]
        == {}
    )
    assert SharedArrangementSnapshot.objects.get().snapshot == snapshot
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = []
    assert read(admin, lab)["allowed_actions"] == ["withdraw"]
    post(admin, f"living-labs/{lab['id']}/runs/", command(lab["revision"]), 403)


@pytest.mark.django_db
def test_lost_ack_creation_recovers_from_group_and_topology_change_requires_fresh_consent(
    context,
):
    _, admin, member, prop, group, _ = context
    lab = ready(context)
    creation = IdempotencyRecord.objects.get(
        user=admin, operation=f"living_lab.create:{group.id}"
    )
    lookup = authenticated(admin).get(
        API + f"rental-operations/{creation.request_key}/?subject_id={group.id}"
    )
    assert lookup.status_code == 200, lookup.data
    assert lookup.data["status"] == "confirmed"
    assert lookup.data["operation_receipt"]["subject_id"] == lab["id"]
    lab = respond(admin, lab)
    # A room change without changing offer terms must still invalidate the immutable computation.
    prop.rental_inventory["rooms"][0]["capacity"] = 1
    prop.save()
    stale = read(member, lab)
    assert (
        stale["latest_run"]["outcome"] == "stale"
        and stale["status"] == "needs_revision"
    )
    current = lab["latest_run"]
    post(
        member,
        f"living-labs/{lab['id']}/responses/",
        command(
            lab["revision"],
            input_revision=lab["input_revision"],
            run_id=current["id"],
            candidate_id=current["candidates"][0]["id"],
            decision="accept",
        ),
        409,
    )


@pytest.mark.django_db
def test_scenario_limit_crosses_lab_ids_and_request_recovery_respects_membership_period(
    context,
):
    _, admin, member, _, group, _ = context
    for _ in range(2):
        lab = create_lab(context)
        for _ in range(3):
            lab = requirements(admin, lab)
            lab = post(
                admin, f"living-labs/{lab['id']}/runs/", command(lab["revision"])
            ).data["resource"]
    another = create_lab(context)
    post(admin, f"living-labs/{another['id']}/runs/", command(another["revision"]), 409)
    body = command(another["revision"], status="omitted", values={})
    post(member, f"living-labs/{another['id']}/my-requirements/", body)
    lookup_path = (
        API + f"rental-operations/{body['request_key']}/?subject_id={another['id']}"
    )
    assert authenticated(member).get(lookup_path).status_code == 200
    GroupMembership.objects.filter(group=group, user=member).update(
        joined_revision=group.revision + 5
    )
    assert authenticated(member).get(lookup_path).status_code == 404
