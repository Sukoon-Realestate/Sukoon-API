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
def test_manual_archive_and_restore_are_retired(rental_participants):
    _, admin, _, prop, _ = rental_participants
    group = create_group(admin, prop)
    client = authenticated(admin)
    assert "archive" not in group["allowed_actions"]
    for action in ("archive", "unarchive"):
        grant = client.get(
            API + "planning-capabilities/",
            {
                "capability": "housing_groups",
                "action": action,
                "subject_id": group["id"],
            },
        )
        assert grant.json()["data"]["allowed_actions"] == []
        post(
            admin,
            f"housing-groups/{group['id']}/{action}/",
            command(
                group["revision"],
                roster_revision=group["roster_revision"],
                action=action,
            ),
            403,
        )
    stored = HousingGroup.objects.get(id=group["id"])
    assert stored.status == "active"
    assert stored.revision == group["revision"]


@pytest.mark.django_db
def test_retiring_archives_restores_populated_groups_without_reviving_invites(
    rental_participants,
):
    from importlib import import_module
    from types import SimpleNamespace
    from django.apps import apps
    from django.db import connection

    _, admin, member, prop, _ = rental_participants
    group = create_group(admin, prop)
    add_member(group, member)
    stored = HousingGroup.objects.get(id=group["id"])
    # A previously archived group, before deploying the retirement migration.
    stored.status = "archived"
    stored.save(update_fields=["status"])
    invitation = GroupInvitation.objects.create(
        group=stored,
        status="revoked",
        nonce="x" * 64,
        expires_at=timezone.now() + timedelta(days=1),
    )
    empty = HousingGroup.objects.create(name="Departed group", status="archived")
    GroupMembership.objects.create(group=empty, user=admin, status="left")
    restore = import_module(
        "core_apps.features.migrations.0020_retire_group_archiving"
    ).restore_populated_groups
    restore(apps, SimpleNamespace(connection=connection))
    stored.refresh_from_db()
    assert stored.status == "active"
    assert stored.revision == group["revision"] + 1
    assert stored.roster_revision == group["roster_revision"] + 1
    assert stored.memberships.filter(status="active").count() == 2
    assert stored.memberships.get(user=admin).role == "admin"
    invitation.refresh_from_db()
    assert invitation.status == "revoked"
    empty.refresh_from_db()
    assert empty.status == "archived"
    assert empty.memberships.get(user=admin).status == "left"
    # Re-running the migration cannot bump revisions or revive old invitations.
    restore(apps, SimpleNamespace(connection=connection))
    stored.refresh_from_db()
    assert stored.revision == group["revision"] + 1
    response = authenticated(admin).get(API + "housing-groups/")
    assert response.status_code == 200
    assert [row["id"] for row in response.json()["data"]] == [group["id"]]
    assert response.json()["data"][0]["status"] == "active"
    assert int(response["X-Total-Count"]) == 1
    assert "edit" in planning_actions(admin, "housing_groups", group["id"])


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
