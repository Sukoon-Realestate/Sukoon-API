"""Canonical shortlist history and the distinction between roster and group revisions."""

import pytest
from .test_student_housing import (
    API,
    student_capabilities,
    group,
    create_plan,
    post,
    read,
    requirements,
    plan_body,
)
from .test_rental_phase2 import rental_participants, authenticated
from .test_rental_lifecycle import command
from .test_planning_cycles import join_group
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from core_apps.features.models import GroupMembership


def act(actor, group, action, plan=None, **values):
    state = authenticated(actor).get(API + f"housing-groups/{group.id}/").data
    body = command(
        state["revision"],
        roster_revision=state["roster_revision"],
        action=action,
        consent=False,
        **values,
    )
    if action in {"vote", "comment", "remove_shortlist"}:
        item = state["shortlist"][0]
        body.update(item_id=item["id"], item_revision=item["revision"])
    if plan:
        body.update(
            academic_plan_id=plan["id"], academic_revision=plan["requirements_revision"]
        )
    return post(actor, f"housing-groups/{group.id}/{action}/", body).data["resource"]


@pytest.mark.django_db
def test_same_shortlist_has_separate_period_votes_and_retains_revision_history(
    rental_participants, group
):
    _, tenant, member, prop, offer_id = rental_participants
    _, selection = resolve_offer_snapshot(prop, offer_id, 2)
    selection["bed_id"] = selection["bed_name"] = ""
    act(tenant, group, "add_shortlist", selection=selection)
    act(tenant, group, "vote", vote="interested")
    first = create_plan(tenant, prop, group=group, people=[tenant, member])
    second = create_plan(
        tenant, prop, group=group, people=[tenant, member], label="Next academic period"
    )
    act(tenant, group, "add_shortlist", first, selection=selection)
    act(tenant, group, "vote", first, vote="maybe")
    act(tenant, group, "comment", first, note="First period discussion")
    act(tenant, group, "add_shortlist", second, selection=selection)
    result = act(member, group, "vote", second, vote="not_suitable")
    assert len(result["shortlist"]) == 1 and group.memberships.count() == 2
    item = result["shortlist"][0]
    assert item["vote_counts"]["interested"] == 1 and item["comments"] == []
    decisions = {row["plan_id"]: row for row in item["academic_decisions"]}
    assert decisions[first["id"]]["vote_counts"]["maybe"] == 1
    assert decisions[second["id"]]["vote_counts"]["maybe"] == 0
    assert decisions[second["id"]]["comments"] == []
    assert "votes_by_user" not in str(item) and "participant_ids" not in str(item)
    requirements(tenant, first, study_space="A changed study requirement")
    result = authenticated(tenant).get(API + f"housing-groups/{group.id}/").data
    history = next(
        row
        for row in result["shortlist"][0]["academic_decisions"]
        if row["plan_id"] == first["id"]
    )
    assert not history["current"] and history["comments"] == ["First period discussion"]
    result = act(tenant, group, "remove_shortlist", second)
    assert len(result["shortlist"]) == 1
    assert result["shortlist"][0]["academic_plan_ids"] == [first["id"]]
    assert result["shortlist"][0]["vote_counts"]["interested"] == 1


@pytest.mark.django_db
def test_late_joined_member_can_plan_but_rejoin_does_not_restore_old_period_access(
    rental_participants, group
):
    _, tenant, member, prop, offer_id = rental_participants
    # Existing edits/votes advance group revision independently of roster changes.
    group.revision, group.roster_revision = 45, 2
    group.save()
    GroupMembership.objects.filter(group=group, user=member).update(joined_revision=40)
    plan = create_plan(tenant, prop, group=group, people=[tenant, member])
    _, selection = resolve_offer_snapshot(prop, offer_id, 2)
    selection["bed_id"] = selection["bed_name"] = ""
    act(tenant, group, "add_shortlist", plan, selection=selection)
    act(member, group, "comment", plan, note="Earlier membership discussion")
    assert read(member, plan["id"])["id"] == plan["id"]
    assert (
        authenticated(member).get(API + "academic-plans/").data["results"][0]["id"]
        == plan["id"]
    )
    state = act(member, group, "leave")
    state = authenticated(tenant).get(API + f"housing-groups/{group.id}/").data
    join_group(tenant, member, state)
    assert (
        authenticated(member).get(API + f"academic-plans/{plan['id']}/").status_code
        == 404
    )
    assert authenticated(member).get(API + "academic-plans/").data["results"] == []
    group.refresh_from_db()
    following = create_plan(tenant, prop, group=group, people=[tenant, member])
    assert read(member, following["id"])["id"] == following["id"]
    assert group.memberships.count() == 2
    body = plan_body(tenant, prop, group=group, people=[tenant, member])
    body["expected_revision"] = plan["revision"]
    post(tenant, f"academic-plans/{plan['id']}/edit/", body)
    assert read(member, plan["id"])["id"] == plan["id"]
    visible = authenticated(member).get(API + f"housing-groups/{group.id}/").data
    assert "Earlier membership discussion" not in str(visible)
