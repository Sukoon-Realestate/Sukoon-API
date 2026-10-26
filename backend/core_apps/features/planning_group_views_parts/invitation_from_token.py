"""Planning group views: invitation from token."""

import base64
import hashlib
import hmac
import uuid
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from ..planning_models import GroupInvitation, GroupProcess
from ..services.planning import require_planning, selection
from ..services.rental_phase2 import RentalConflict
from .process_payload import active_ids
from .dispatch_process import _dispatch_process


def _submit_process(request, group, action):
    kind = "visit" if action == "request_visit" else "application"
    require_planning(
        request.user, "group_visits" if kind == "visit" else "group_applications"
    )
    from ..services.student_housing.groups import context, participant_ids
    from ..services.student_housing.publication import preview

    academic = context(request.user, group, request.data)
    members = participant_ids(academic) if academic else active_ids(group)
    supplied = request.data.get("participant_ids", [])
    if (
        not isinstance(supplied, list)
        or any(not isinstance(x, str) for x in supplied)
        or len(set(supplied)) != len(supplied)
        or (not academic and str(request.user.id) not in supplied)
        or not set(supplied).issubset(members)
        or (kind == "application" and sorted(supplied) != members)
    ):
        raise RentalConflict(
            "The participants must match the current active roster.",
            code="roster_changed",
        )
    members = sorted(supplied)
    prop, snapshot = selection(request, request.data.get("selection"))
    if prop.owner_id in group.memberships.filter(status="active").values_list(
        "user_id", flat=True
    ):
        raise PermissionDenied(
            "An owner cannot submit a tenant group process to themselves."
        )
    capacity = 1 if snapshot["rental_scope"] == "bed" else snapshot.get("capacity")
    if capacity is None:
        raise RentalConflict(
            "The owner must confirm accommodation capacity before a group application or viewing.",
            code="capacity_unknown",
        )
    if len(members) > capacity:
        raise ValidationError(
            {"selection": "Selected accommodation cannot hold this group."}
        )
    if kind != "visit":
        proposals = [
            x
            for x in group.proposals
            if x["offer_id"] == snapshot["offer_id"]
            and x["offer_revision"] == snapshot["offer_revision"]
            and x["roster_revision"] == group.roster_revision
            and set(x["approved_by"]) == set(members)
            and x.get("academic_plan_id") == (str(academic.id) if academic else None)
            and (
                not academic
                or x.get("academic_revision") == academic.requirements_revision
            )
        ]
        if not proposals:
            raise RentalConflict(
                "Every current member must approve this offer's cost proposal first.",
                code="consent_required",
            )
    if group.processes.filter(
        kind=kind,
        proposal_snapshot=(
            {
                "visit_note": serializers.CharField(
                    allow_blank=True, max_length=1000
                ).run_validation(request.data.get("note", ""))
            }
            if kind == "visit"
            else {}
        ),
        academic_plan=academic,
        status__in=[
            "collecting_consent",
            "ready",
            "submitted",
            "scheduled",
            "under_review",
            "approved_to_proceed",
        ],
    ).exists():
        raise RentalConflict("Resolve the current group process first.")
    academic_snapshot = preview(academic) if academic else {}
    if academic:
        from ..services.student_housing.groups import source_snapshot

        academic_snapshot.update(
            source_snapshot(request.user, group, academic, snapshot)
        )
    item = GroupProcess.objects.create(
        academic_plan=academic,
        academic_revision=academic.requirements_revision if academic else None,
        academic_snapshot=academic_snapshot,
        group=group,
        property=prop,
        initiated_by=request.user,
        kind=kind,
        proposal_snapshot=(
            {
                "visit_note": serializers.CharField(
                    allow_blank=True, max_length=1000
                ).run_validation(request.data.get("note", ""))
            }
            if kind == "visit"
            else {}
        ),
        roster_revision=group.roster_revision,
        access_group_revision=group.revision,
        selection=snapshot,
        participant_ids=members,
        consented_ids=(
            [str(request.user.id)]
            if request.data.get("consent") is True and str(request.user.id) in members
            else []
        ),
    )
    if item.consented_ids == members:
        _dispatch_process(request, group, item)


def invitation_token(item):
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        f"group-invite:{item.id}:{item.nonce}".encode(),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(item.id.bytes + signature).rstrip(b"=").decode()


def invitation_from_token(token):
    try:
        if not isinstance(token, str) or len(token) != 64:
            raise ValueError
        raw = base64.urlsafe_b64decode(token)
        item = GroupInvitation.objects.select_related("group").get(
            id=uuid.UUID(bytes=raw[:16])
        )
        if not hmac.compare_digest(token, invitation_token(item)):
            raise ValueError
    except (ValueError, TypeError, GroupInvitation.DoesNotExist):
        raise NotFound()
    if (
        item.status != "active"
        or item.expires_at <= timezone.now()
        or item.group.status != "active"
    ):
        raise RentalConflict(
            "This invitation expired or was revoked.", code="invitation_unavailable"
        )
    return item


def invitation_payload(item, *, include_link=True):
    return {
        "id": str(item.id),
        "group_id": str(item.group.id),
        "group_name": item.group.name,
        "status": "expired" if item.expires_at <= timezone.now() else item.status,
        "link": (
            f"https://sokoun.app/housing-groups/join#{invitation_token(item)}"
            if include_link and item.status == "active"
            else ""
        ),
        "revision": item.revision,
        "group_revision": item.group.revision,
        "member_count": item.group.memberships.filter(status="active").count(),
        "capacity": item.group.capacity,
        "expires_at": item.expires_at.isoformat(),
    }
