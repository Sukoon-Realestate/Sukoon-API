"""Planning group views: group payload."""

import secrets
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from ..planning_models import GroupInvitation
from ..services.planning import (
    check_revision,
    criteria_payload,
    display_name,
    mutate,
    planning_api,
)
from .process_payload import group_for, group_actions, active_ids, process_payload
from .invitation_from_token import invitation_from_token, invitation_payload


@planning_api(["POST"], "housing_groups")
def group_invitation_create(request, group_id):
    def apply(group, revision):
        if "create_invite" not in group_actions(request.user, group):
            raise PermissionDenied("Only the group administrator can invite members.")
        if str(request.data.get("group_id")) != str(group.id):
            raise ValidationError({"group_id": "Must match the route."})
        check_revision(group.revision, request.data.get("group_revision"))
        return GroupInvitation.objects.create(
            group=group,
            nonce=secrets.token_hex(32),
            expires_at=timezone.now() + timedelta(days=7),
        )

    return mutate(
        request,
        f"group.invite.{group_id}",
        lambda: group_for(request.user, group_id, lock=True),
        apply,
        invitation_payload,
        creating=True,
    )


@planning_api(["GET"], "housing_groups")
def group_invitation_detail(request, invitation_id):
    item = get_object_or_404(
        GroupInvitation.objects.select_related("group"), id=invitation_id
    )
    if "read_invite" not in group_actions(request.user, item.group):
        raise NotFound()
    return Response(invitation_payload(item))


@planning_api(["POST"], "housing_groups")
def group_invitation_preview(request):
    return Response(
        invitation_payload(
            invitation_from_token(request.data.get("token")), include_link=False
        )
    )


def join_payload(item, user):
    admin = item.group.memberships.filter(
        user=user, status="active", role="admin"
    ).exists()
    return {
        "id": str(item.id),
        "group_id": str(item.group.id),
        "group_name": item.group.name,
        "user_id": str(item.user.id),
        "name": display_name(item.user),
        "note": item.note,
        "revision": item.revision,
        "status": item.status,
        "allowed_actions": (
            (["approve", "decline"] if admin else ["withdraw"])
            if item.status == "pending"
            else []
        ),
    }


def group_payload(group, user):
    if not group.memberships.filter(user=user, status="active").exists():
        return {
            "id": str(group.id),
            "revision": group.revision,
            "roster_revision": group.roster_revision,
            "status": "archived",
            "members": [],
            "shortlist": [],
            "proposals": [],
            "visits": [],
            "applications": [],
            "allowed_actions": [],
            "blocking_reasons": ["Group membership ended."],
        }
    member = group.memberships.get(user=user, status="active")
    shortlist = [
        {
            **x,
            "votes": len(x.get("voter_ids", [])),
            "comments": [
                c["text"]
                for c in x.get("comments", [])
                if c.get("group_revision", 0) >= member.joined_revision
            ],
            "vote_counts": {
                choice: [
                    vote
                    for actor, vote in x.get("votes_by_user", {}).items()
                    if actor in active_ids(group)
                ].count(choice)
                for choice in ("interested", "maybe", "not_suitable")
            },
            "my_vote": x.get("votes_by_user", {}).get(str(user.id), ""),
            "abstentions": len(active_ids(group))
            - len(set(x.get("votes_by_user", {})) & set(active_ids(group))),
        }
        for x in group.shortlist
    ]
    for item in shortlist:
        item.pop("voter_ids", None)
        item.pop("votes_by_user", None)
    return {
        "id": str(group.id),
        "name": group.name,
        "status": group.status,
        "visibility": group.visibility,
        "revision": group.revision,
        "roster_revision": group.roster_revision,
        "capacity": group.capacity,
        "criteria": criteria_payload(group.criteria),
        "members": [
            {
                "user_id": str(x.user.id),
                "name": display_name(x.user),
                "role": x.role,
                "status": x.status,
            }
            for x in group.memberships.select_related("user").order_by("pkid")
        ],
        "shortlist": shortlist,
        "proposals": [
            x for x in group.proposals if str(user.id) in x.get("contributions", {})
        ],
        "join_requests": (
            [
                join_payload(x, user)
                for x in group.join_requests.filter(status="pending")
            ]
            if member.role == "admin"
            else []
        ),
        "visits": [
            process_payload(x, user)
            for x in group.processes.filter(kind="visit")
            .select_related("visit", "interest")
            .order_by("pkid")
            if str(user.id) in x.participant_ids
        ],
        "applications": [
            process_payload(x, user)
            for x in group.processes.filter(kind="application")
            .select_related("visit", "interest")
            .order_by("pkid")
            if str(user.id) in x.participant_ids
        ],
        "allowed_actions": group_actions(user, group),
        "blocking_reasons": [],
    }
