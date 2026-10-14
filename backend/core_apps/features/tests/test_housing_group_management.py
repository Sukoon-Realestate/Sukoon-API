"""Regression coverage for mobile group management and tenant badges."""

import uuid
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from core_apps.features.planning_models import (
    GroupInvitation,
    GroupJoinRequest,
    GroupMembership,
    HousingGroup,
)
from core_apps.features.services.planning_access import planning_actions
from .test_funded_settlement import command
from .test_rental_phase2 import authenticated, rental_participants
from .test_planning_cycles import (
    API,
    configured_planning_offer,
    create_group,
    group_action,
    post,
)


def add_member(group, user):
    return GroupMembership.objects.create(
        group_id=HousingGroup.objects.get(id=group["id"]).pk, user=user
    )


@pytest.mark.django_db
def test_archive_filter_restore_and_old_invites_stay_revoked(rental_participants):
    _, admin, member, prop, _ = rental_participants
    group = create_group(admin, prop)
    add_member(group, member)
    invitation = post(
        admin,
        f"housing-groups/{group['id']}/invitations/",
        command(group_id=group["id"], group_revision=group["revision"]),
        201,
    ).data["resource"]
    archived = group_action(admin, group, "archive")
    assert archived["status"] == "archived"
    assert "unarchive" in archived["allowed_actions"]
    assert "unarchive" in planning_actions(admin, "housing_groups", group["id"])
    assert "unarchive" not in planning_actions(member, "housing_groups", group["id"])
    active_list = authenticated(admin).get(
        API + "housing-groups/", {"status": "active"}
    )
    assert active_list.data["results"] == []
    archived_list = authenticated(admin).get(
        API + "housing-groups/", {"status": "archived"}
    )
    assert [x["id"] for x in archived_list.data["results"]] == [group["id"]]
    body = command(
        archived["revision"],
        roster_revision=archived["roster_revision"],
        action="unarchive",
    )
    post(member, f"housing-groups/{group['id']}/unarchive/", body, 403)
    restored = post(admin, f"housing-groups/{group['id']}/unarchive/", body).data
    assert restored["resource"]["status"] == "active"
    assert restored["resource"]["revision"] == archived["revision"] + 1
    assert (
        post(admin, f"housing-groups/{group['id']}/unarchive/", body).data == restored
    )
    assert GroupInvitation.objects.get(id=invitation["id"]).status == "revoked"


@pytest.mark.django_db
def test_admin_leave_selects_successor_atomically_and_replays(rental_participants):
    _, admin, member, prop, _ = rental_participants
    group = create_group(admin, prop)
    add_member(group, member)
    missing = command(
        group["revision"], roster_revision=group["roster_revision"], action="leave"
    )
    post(admin, f"housing-groups/{group['id']}/leave/", missing, 400)
    assert HousingGroup.objects.get(id=group["id"]).revision == group["revision"]
    invalid = command(
        group["revision"],
        roster_revision=group["roster_revision"],
        action="leave",
        member_id=str(admin.id),
    )
    post(admin, f"housing-groups/{group['id']}/leave/", invalid, 400)
    body = command(
        group["revision"],
        roster_revision=group["roster_revision"],
        action="leave",
        member_id=str(member.id),
    )
    result = post(admin, f"housing-groups/{group['id']}/leave/", body).data
    assert post(admin, f"housing-groups/{group['id']}/leave/", body).data == result
    stored = HousingGroup.objects.get(id=group["id"])
    assert stored.status == "active"
    assert stored.memberships.get(user=member).role == "admin"
    assert stored.memberships.get(user=admin).status == "left"
    assert stored.revision == group["revision"] + 1
    assert stored.roster_revision == group["roster_revision"] + 1
    assert (
        authenticated(admin).get(API + f"housing-groups/{group['id']}/").status_code
        == 404
    )


@pytest.mark.django_db
def test_last_admin_leave_archives_and_ordinary_member_cannot_transfer(
    rental_participants,
):
    _, admin, member, prop, _ = rental_participants
    group = create_group(admin, prop)
    add_member(group, member)
    group = group_action(member, group, "leave", member_id=str(member.id))
    stored = HousingGroup.objects.get(id=group["id"])
    assert stored.memberships.get(user=admin).role == "admin"
    # A departed member's response is deliberately redacted; refresh as admin.
    group = authenticated(admin).get(API + f"housing-groups/{stored.id}/").data
    group_action(admin, group, "leave")
    stored.refresh_from_db()
    assert stored.status == "archived"
    assert not stored.memberships.filter(status="active").exists()


@pytest.mark.django_db
def test_invitation_links_list_is_admin_only_with_expired_and_revoked_history(
    rental_participants,
):
    owner, admin, member, prop, _ = rental_participants
    group = create_group(admin, prop)
    add_member(group, member)
    stored = HousingGroup.objects.get(id=group["id"])
    for status, days in [("active", 1), ("active", -1), ("revoked", 1)]:
        GroupInvitation.objects.create(
            group=stored,
            nonce=uuid.uuid4().hex,
            status=status,
            expires_at=timezone.now() + timedelta(days=days),
        )
    endpoint = API + f"housing-groups/{group['id']}/invitations/"
    response = authenticated(admin).get(endpoint)
    assert response.status_code == 200
    assert {x["status"] for x in response.data["results"]} == {
        "active",
        "expired",
        "revoked",
    }
    assert authenticated(member).get(endpoint).status_code == 404
    assert authenticated(owner).get(endpoint).status_code == 404


@pytest.mark.django_db
def test_tenant_join_badge_counts_only_pending_requests_for_active_admin_groups(
    rental_participants,
):
    owner, admin, member, prop, _ = rental_participants
    group = create_group(admin, prop)
    stored = HousingGroup.objects.get(id=group["id"])
    request = GroupJoinRequest.objects.create(group=stored, user=member)
    url = reverse("tenant-unread-counts")
    assert (
        authenticated(admin).get(url).json()["data"]["group_join_requests_count"] == 1
    )
    assert (
        authenticated(member).get(url).json()["data"]["group_join_requests_count"] == 0
    )
    assert (
        authenticated(owner).get(url).json()["data"]["group_join_requests_count"] == 0
    )
    request.status = "declined"
    request.save()
    assert (
        authenticated(admin).get(url).json()["data"]["group_join_requests_count"] == 0
    )
    request.status = "pending"
    request.save()
    stored.status = "archived"
    stored.save()
    assert (
        authenticated(admin).get(url).json()["data"]["group_join_requests_count"] == 0
    )
