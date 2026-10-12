import base64
import hashlib
import hmac
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from core_apps.properties.services.visit import PropertyVisitService
from .models import RentalInterest
from .planning_models import (
    GroupInvitation,
    GroupMembership,
    GroupProcess,
    HousingGroup,
)
from .services.commands import money_minor
from .services.planning import (
    check_revision,
    civil_date,
    criteria,
    criteria_payload,
    display_name,
    mutate,
    offer_money,
    page,
    planning_api,
    require_planning,
    selection,
    text_field,
)
from .services.rental_phase2 import RentalConflict


def group_for(user, identifier, *, lock=False, departed=False):
    queryset = (
        HousingGroup.objects.select_for_update() if lock else HousingGroup.objects.all()
    )
    item = get_object_or_404(queryset, id=identifier)
    if not item.memberships.filter(
        user=user, status__in=["active", "left"] if departed else ["active"]
    ).exists():
        raise NotFound()
    return item


def group_actions(user, group):
    member = group.memberships.filter(user=user, status="active").first()
    if not member or group.status != "active":
        return []
    actions = [
        "leave",
        "add_shortlist",
        "vote",
        "comment",
        "propose_costs",
        "approve_costs",
        "consent_visit",
        "withdraw_visit_consent",
        "consent_application",
        "withdraw_application_consent",
    ]
    if member.role == "admin":
        actions += [
            "edit",
            "transfer_admin",
            "remove_member",
            "archive",
            "revoke_invites",
            "create_invite",
            "read_invite",
            "remove_shortlist",
            "request_visit",
            "apply",
        ]
    return actions


def active_ids(group):
    return sorted(
        str(x)
        for x in group.memberships.filter(status="active").values_list(
            "user__id", flat=True
        )
    )


def process_payload(item, user):
    status = item.status
    if item.visit_id and status in {"submitted", "scheduled"}:
        status = {
            "pending": "submitted",
            "confirmed": "scheduled",
            "rejected": "rejected",
            "canceled": "withdrawn",
        }[item.visit.status]
    if item.interest_id and status == "submitted":
        status = {
            "rejected": "rejected",
            "withdrawn": "withdrawn",
            "invited": "completed",
        }.get(item.interest.status, status)
    actor_id = str(user.id)
    actions = []
    if (
        status in {"collecting_consent", "ready", "submitted", "scheduled"}
        and actor_id in item.participant_ids
    ):
        suffix = "visit" if item.kind == "visit" else "application"
        actions = (
            [f"withdraw_{suffix}_consent"]
            if actor_id in item.consented_ids
            else [f"consent_{suffix}"]
        )
    return {
        "id": str(item.id),
        "revision": item.revision,
        "roster_revision": item.roster_revision,
        "status": status,
        "selection": item.selection,
        "participant_ids": item.participant_ids,
        "consented_ids": item.consented_ids,
        "appointment_at": (
            item.appointment_at.isoformat() if item.appointment_at else ""
        ),
        "qualifying_visit_id": str(item.visit.id) if item.visit_id else "",
        "interest_id": str(item.interest.id) if item.interest_id else "",
        "allowed_actions": actions,
        "blocking_reasons": [],
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
    shortlist = [
        {
            **x,
            "votes": len(x.get("voter_ids", [])),
            "comments": [c["text"] for c in x.get("comments", [])],
        }
        for x in group.shortlist
    ]
    for item in shortlist:
        item.pop("voter_ids", None)
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
        "proposals": group.proposals,
        "visits": [
            process_payload(x, user)
            for x in group.processes.filter(kind="visit")
            .select_related("visit", "interest")
            .order_by("pkid")
        ],
        "applications": [
            process_payload(x, user)
            for x in group.processes.filter(kind="application")
            .select_related("visit", "interest")
            .order_by("pkid")
        ],
        "allowed_actions": group_actions(user, group),
        "blocking_reasons": [],
    }


def _group_values(data):
    if data.get("visibility", "invite_only") not in {"invite_only", "private"}:
        raise ValidationError({"visibility": "Groups are private or invite_only."})
    capacity = data.get("capacity")
    if type(capacity) is not int or not 2 <= capacity <= 20:
        raise ValidationError({"capacity": "Use an integer between 2 and 20."})
    return {
        "name": text_field(data, "name", required=True, limit=160),
        "visibility": data.get("visibility", "invite_only"),
        "capacity": capacity,
        "criteria": criteria(data.get("criteria")),
    }


@planning_api(["GET", "POST"], "housing_groups")
def housing_groups(request):
    if request.method == "GET":
        return page(
            request,
            HousingGroup.objects.filter(
                memberships__user=request.user, memberships__status="active"
            ).order_by("-created_at", "pkid"),
            lambda x: group_payload(x, request.user),
        )

    def apply(_, revision):
        if (
            request.data.get("action") != "create"
            or request.data.get("roster_revision") != 0
        ):
            raise ValidationError("New groups use action=create and roster_revision=0.")
        group = HousingGroup.objects.create(**_group_values(request.data))
        GroupMembership.objects.create(group=group, user=request.user, role="admin")
        return group

    return mutate(
        request,
        "group.create",
        lambda: None,
        apply,
        lambda x: group_payload(x, request.user),
        creating=True,
    )


@planning_api(["GET"], "housing_groups")
def housing_group_detail(request, group_id):
    return Response(group_payload(group_for(request.user, group_id), request.user))


def invalidate_process(item):
    if item.visit_id and item.visit.status in {"pending", "confirmed"}:
        item.visit.status = "canceled"
        item.visit.note = (
            "Group consent or roster changed. Submit a new reviewed group visit."
        )
        item.visit.save(update_fields=["status", "note", "updated_at"])
    if item.interest_id and item.interest.status not in {"rejected", "withdrawn"}:
        if item.interest.invitations.filter(
            status__in=["pending", "accepted"]
        ).exists():
            raise RentalConflict(
                "A tenancy invitation already uses this application; resolve it before changing participants."
            )
        item.interest.status = "withdrawn"
        item.interest.revision += 1
        item.interest.save()
    item.consented_ids = []
    item.status = "withdrawn"
    item.revision += 1
    item.save()


def invalidate_roster(group):
    group.roster_revision += 1
    for proposal in group.proposals:
        proposal["approved_by"] = []
        proposal["revision"] += 1
    for item in group.processes.exclude(
        status__in=["withdrawn", "expired", "rejected", "completed"]
    ):
        invalidate_process(item)


def _shortlist_item(group, data):
    item = next((x for x in group.shortlist if x["id"] == data.get("item_id")), None)
    if not item:
        raise ValidationError({"item_id": "Choose a persisted shortlist item."})
    check_revision(item["revision"], data.get("item_revision"))
    return item


def _proposal(request, group):
    raw = request.data.get("proposal")
    if not isinstance(raw, dict):
        raise ValidationError({"proposal": "Supply a cost proposal."})
    check_revision(group.roster_revision, raw.get("roster_revision"))
    shortlisted = next(
        (
            x
            for x in group.shortlist
            if x["selection"]["offer_id"] == raw.get("offer_id")
        ),
        None,
    )
    if not shortlisted:
        raise ValidationError({"proposal": "Use a currently shortlisted offer."})
    _, snapshot = selection(request, shortlisted["selection"])
    check_revision(snapshot["offer_revision"], raw.get("offer_revision"))
    total = money_minor(raw.get("total"))
    rent, _ = offer_money(snapshot)
    if total != rent or raw.get("period") != snapshot["terms"].get("price_period"):
        raise ValidationError(
            {
                "total": "The contribution total and period must equal the selected offer rent."
            }
        )
    members = active_ids(group)
    contributions = raw.get("contributions")
    if (
        not isinstance(contributions, dict)
        or set(contributions) != set(members)
        or any(type(x) is not int or x < 0 for x in contributions.values())
        or sum(contributions.values()) != total
    ):
        raise ValidationError(
            {
                "contributions": "Every active member needs a nonnegative integer contribution; their sum must equal total."
            }
        )
    start = civil_date(raw.get("start_on"), "start_on", future=True)
    end = civil_date(raw["end_on"], "end_on") if raw.get("end_on") else None
    if end and end <= start:
        raise ValidationError({"end_on": "Must follow start_on."})
    previous = next((x for x in group.proposals if x["id"] == raw.get("id")), None)
    check_revision(previous["revision"] if previous else 0, raw.get("revision", 0))
    value = {
        "id": previous["id"] if previous else str(uuid.uuid4()),
        "revision": previous["revision"] + 1 if previous else 1,
        "roster_revision": group.roster_revision,
        "offer_id": snapshot["offer_id"],
        "offer_revision": snapshot["offer_revision"],
        "start_on": str(start),
        "end_on": str(end) if end else "",
        "period": raw["period"],
        "total": raw["total"],
        "contributions": contributions,
        "approved_by": [],
    }
    if previous:
        group.proposals[group.proposals.index(previous)] = value
    else:
        group.proposals.append(value)
    for process in group.processes.filter(kind="application").exclude(
        status__in=["withdrawn", "expired", "rejected"]
    ):
        invalidate_process(process)


def _submit_process(request, group, action):
    kind = "visit" if action == "request_visit" else "application"
    require_planning(
        request.user, "group_visits" if kind == "visit" else "group_applications"
    )
    members = active_ids(group)
    supplied = request.data.get("participant_ids", [])
    if (
        not isinstance(supplied, list)
        or any(not isinstance(x, str) for x in supplied)
        or sorted(supplied) != members
    ):
        raise RentalConflict(
            "The participants must match the current active roster.",
            code="roster_changed",
        )
    prop, snapshot = selection(request, request.data.get("selection"))
    if prop.owner_id in group.memberships.filter(status="active").values_list(
        "user_id", flat=True
    ):
        raise PermissionDenied(
            "An owner cannot submit a tenant group process to themselves."
        )
    capacity = 1 if snapshot["rental_scope"] == "bed" else snapshot.get("capacity")
    if capacity is not None and len(members) > capacity:
        raise ValidationError(
            {"selection": "Selected accommodation cannot hold this group."}
        )
    appointment = None
    if kind == "visit":
        appointment = parse_datetime(request.data.get("appointment_at", ""))
        if (
            not appointment
            or timezone.is_naive(appointment)
            or appointment <= timezone.now()
        ):
            raise ValidationError(
                {"appointment_at": "Use a future timezone-aware ISO timestamp."}
            )
    else:
        proposals = [
            x
            for x in group.proposals
            if x["offer_id"] == snapshot["offer_id"]
            and x["offer_revision"] == snapshot["offer_revision"]
            and x["roster_revision"] == group.roster_revision
            and set(x["approved_by"]) == set(members)
        ]
        if not proposals:
            raise RentalConflict(
                "Every current member must approve this offer's cost proposal first.",
                code="consent_required",
            )
    if group.processes.filter(
        kind=kind, status__in=["collecting_consent", "ready", "submitted", "scheduled"]
    ).exists():
        raise RentalConflict("Resolve the current group process first.")
    item = GroupProcess.objects.create(
        group=group,
        property=prop,
        initiated_by=request.user,
        kind=kind,
        roster_revision=group.roster_revision,
        selection=snapshot,
        participant_ids=members,
        consented_ids=(
            [str(request.user.id)] if request.data.get("consent") is True else []
        ),
        appointment_at=appointment,
    )
    if item.consented_ids == members:
        _dispatch_process(request, group, item)


def _dispatch_process(request, group, item):
    prop, snapshot = selection(request, item.selection)
    if item.kind == "visit":
        local = timezone.localtime(item.appointment_at)
        item.visit = PropertyVisitService.create_visit(
            item.initiated_by,
            prop,
            {
                "visit_date": local.date(),
                "visit_time": local.time().replace(tzinfo=None),
                "offer_id": snapshot["offer_id"],
                "expected_offer_revision": snapshot["offer_revision"],
                "note": f"Group viewing: {group.name}; {len(item.participant_ids)} consenting members.",
            },
        )
    else:
        proposal = next(
            (
                x
                for x in reversed(group.proposals)
                if x["offer_id"] == snapshot["offer_id"]
                and x["roster_revision"] == group.roster_revision
                and set(x["approved_by"]) == set(item.participant_ids)
            ),
            None,
        )
        if not proposal:
            raise RentalConflict("Cost consent changed.", code="consent_required")
        start = civil_date(proposal["start_on"], "start_on", future=True)
        months = snapshot["terms"].get("rental_period", 1)
        if (
            snapshot["terms"].get("price_period") != "monthly"
            or type(months) is not int
            or months < 1
        ):
            raise ValidationError(
                {
                    "selection": "The agreement workflow currently supports monthly offers."
                }
            )
        if proposal.get("end_on"):
            from dateutil.relativedelta import relativedelta

            end = civil_date(proposal["end_on"], "end_on")
            agreed_months = (end.year - start.year) * 12 + end.month - start.month
            if (
                agreed_months < months
                or start + relativedelta(months=agreed_months) != end
            ):
                raise ValidationError(
                    {
                        "end_on": "Application dates must span whole calendar months and meet the minimum term."
                    }
                )
            months = agreed_months
        item.interest = RentalInterest.objects.create(
            property=prop,
            tenant=item.initiated_by,
            offer_id=snapshot["offer_id"],
            offer_revision=snapshot["offer_revision"],
            offer_snapshot=snapshot,
            desired_start=start,
            months=months,
            occupants=len(item.participant_ids),
            message=f"Reviewed group application {group.id}; member cost consent is not a lease signature.",
        )
    item.status = "submitted"
    item.save()


@planning_api(["POST"], "housing_groups")
def housing_group_action(request, group_id, action):
    def apply(group, revision):
        if request.data.get("action") != action:
            raise ValidationError({"action": "Body and route action must match."})
        if action not in group_actions(request.user, group):
            raise PermissionDenied("This group action is not available to you.")
        check_revision(group.roster_revision, request.data.get("roster_revision"))
        actor_id = str(request.user.id)
        if action == "edit":
            values = _group_values(request.data)
            if values["capacity"] < len(active_ids(group)):
                raise ValidationError(
                    {"capacity": "Capacity cannot be less than the active roster."}
                )
            for key, value in values.items():
                setattr(group, key, value)
        elif action in {"leave", "remove_member", "transfer_admin"}:
            target_id = actor_id if action == "leave" else request.data.get("member_id")
            target = get_object_or_404(
                group.memberships.filter(status="active"), user__id=target_id
            )
            if action == "transfer_admin":
                if target.user_id == request.user.pk:
                    raise ValidationError(
                        {"member_id": "Select another active member."}
                    )
                group.memberships.filter(user=request.user).update(role="member")
                target.role = "admin"
            else:
                if target.role == "admin":
                    raise RentalConflict("Transfer administration before leaving.")
                target.status = "left" if action == "leave" else "removed"
            target.save()
            invalidate_roster(group)
        elif action in {"archive", "revoke_invites"}:
            group.invitations.filter(status="active").update(status="revoked")
            if action == "archive":
                group.status = "archived"
                invalidate_roster(group)
        elif action == "add_shortlist":
            _, snapshot = selection(request, request.data.get("selection"))
            if any(
                x["selection"]["offer_id"] == snapshot["offer_id"]
                and x["selection"]["property_id"] == snapshot["property_id"]
                for x in group.shortlist
            ):
                raise RentalConflict("This accommodation is already shortlisted.")
            group.shortlist.append(
                {
                    "id": str(uuid.uuid4()),
                    "revision": 1,
                    "selection": snapshot,
                    "comments": [],
                    "voter_ids": [],
                }
            )
        elif action in {"remove_shortlist", "vote", "comment"}:
            item = _shortlist_item(group, request.data)
            if action == "remove_shortlist":
                group.shortlist.remove(item)
                group.proposals = [
                    x
                    for x in group.proposals
                    if x["offer_id"] != item["selection"]["offer_id"]
                ]
                for process in group.processes.exclude(
                    status__in=["withdrawn", "expired", "rejected"]
                ):
                    if process.selection["offer_id"] == item["selection"]["offer_id"]:
                        invalidate_process(process)
            elif action == "vote":
                voters = set(item["voter_ids"])
                (
                    voters.add(actor_id)
                    if request.data.get("consent") is True
                    else voters.discard(actor_id)
                )
                item["voter_ids"] = sorted(voters)
                item["revision"] += 1
            else:
                item["comments"].append(
                    {
                        "user_id": actor_id,
                        "text": text_field(
                            request.data, "note", required=True, limit=1000
                        ),
                    }
                )
                item["revision"] += 1
        elif action == "propose_costs":
            _proposal(request, group)
        elif action == "approve_costs":
            item = next(
                (x for x in group.proposals if x["id"] == request.data.get("item_id")),
                None,
            )
            if not item:
                raise ValidationError({"item_id": "Select a persisted proposal."})
            check_revision(item["revision"], request.data.get("item_revision"))
            check_revision(group.roster_revision, item["roster_revision"])
            consent = set(item["approved_by"])
            (
                consent.add(actor_id)
                if request.data.get("consent") is True
                else consent.discard(actor_id)
            )
            item["approved_by"] = sorted(consent)
            item["revision"] += 1
            if request.data.get("consent") is not True:
                for process in group.processes.filter(kind="application").exclude(
                    status__in=["withdrawn", "expired", "rejected"]
                ):
                    invalidate_process(process)
        elif action in {"request_visit", "apply"}:
            _submit_process(request, group, action)
        else:
            kind = "visit" if "visit" in action else "application"
            require_planning(
                request.user,
                "group_visits" if kind == "visit" else "group_applications",
            )
            item = get_object_or_404(
                group.processes.select_for_update(),
                id=request.data.get("item_id"),
                kind=kind,
            )
            check_revision(item.revision, request.data.get("item_revision"))
            check_revision(group.roster_revision, item.roster_revision)
            if action not in process_payload(item, request.user)["allowed_actions"]:
                raise PermissionDenied("This process consent action is unavailable.")
            if action.startswith("withdraw"):
                invalidate_process(item)
            else:
                if request.data.get("consent") is not True:
                    raise ValidationError(
                        {"consent": "Explicit actor consent is required."}
                    )
                item.consented_ids = sorted(set(item.consented_ids) | {actor_id})
                item.revision += 1
                if set(item.consented_ids) == set(item.participant_ids):
                    _dispatch_process(request, group, item)
                item.save()
        group.revision += 1
        group.save()
        return group

    return mutate(
        request,
        f"group.{action}.{group_id}",
        lambda: group_for(
            request.user, group_id, lock=True, departed=action == "leave"
        ),
        apply,
        lambda x: group_payload(x, request.user),
    )


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


@planning_api(["POST"], "housing_groups")
def group_invitation_join(request):
    def load():
        invite = invitation_from_token(request.data.get("token"))
        return HousingGroup.objects.select_for_update().get(pk=invite.group_id)

    def apply(group, revision):
        invitation_from_token(
            request.data.get("token")
        )  # Recheck revocation after lock.
        if str(request.data.get("group_id")) != str(group.id):
            raise ValidationError({"group_id": "Invitation group mismatch."})
        check_revision(group.revision, request.data.get("group_revision"))
        if group.memberships.filter(user=request.user, status="active").exists():
            raise RentalConflict("You are already a member.")
        if group.memberships.filter(user=request.user, status="removed").exists():
            raise PermissionDenied("Removed members cannot reuse an old invitation.")
        if len(active_ids(group)) >= group.capacity:
            raise RentalConflict("The group is full.", code="group_full")
        GroupMembership.objects.update_or_create(
            group=group,
            user=request.user,
            defaults={"role": "member", "status": "active"},
        )
        invalidate_roster(group)
        group.revision += 1
        group.save()
        return group

    return mutate(
        request, "group.join", load, apply, lambda x: group_payload(x, request.user)
    )
