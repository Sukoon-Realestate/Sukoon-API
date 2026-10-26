"""Planning group views: housing group action."""

import uuid
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from ..services.planning import (
    check_revision,
    mutate,
    planning_api,
    require_planning,
    selection,
    text_field,
)
from ..services.rental_phase2 import RentalConflict
from .process_payload import (
    group_for,
    group_actions,
    active_ids,
    process_payload,
    _group_values,
    invalidate_process,
    invalidate_roster,
    _shortlist_item,
)
from .dispatch_process import _proposal, _dispatch_process
from .invitation_from_token import _submit_process
from .group_payload import group_payload


@planning_api(["POST"], "housing_groups")
def housing_group_action(request, group_id, action):
    def apply(group, revision):
        if request.data.get("action") != action:
            raise ValidationError({"action": "Body and route action must match."})
        if action not in group_actions(request.user, group):
            raise PermissionDenied("This group action is not available to you.")
        check_revision(group.roster_revision, request.data.get("roster_revision"))
        if action in {"request_visit", "apply", "propose_costs"}:
            from ..services.student_housing.groups import bind_housing_response
            bind_housing_response(request.user, group, request.data)
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
                    if action != "leave":
                        raise RentalConflict(
                            "Transfer administration before removing an administrator."
                        )
                    successors = group.memberships.filter(status="active").exclude(
                        pk=target.pk
                    )
                    if successors.exists():
                        successor_id = request.data.get("member_id")
                        try:
                            successor_id = uuid.UUID(str(successor_id))
                        except (ValueError, TypeError):
                            raise ValidationError(
                                {"member_id": "Choose an active group member."}
                            )
                        successor = (
                            successors.filter(user__id=successor_id).first()
                            if successor_id
                            else None
                        )
                        if successor is None:
                            raise ValidationError(
                                {
                                    "member_id": "Choose the next administrator from active members."
                                }
                            )
                        # Release the unique active-admin constraint inside the
                        # transaction before assigning the successor.
                        target.role = "member"
                        target.save(update_fields=["role", "updated_at"])
                        successor.role = "admin"
                        successor.save(update_fields=["role", "updated_at"])
                    else:
                        group.status = "archived"
                    group.invitations.filter(status="active").update(status="revoked")
                    target.role = "member"
                target.status = "left" if action == "leave" else "removed"
            target.save()
            invalidate_roster(group)
        elif action == "revoke_invites":
            group.invitations.filter(status="active").update(status="revoked")
        elif action == "add_shortlist":
            _, snapshot = selection(request, request.data.get("selection"))
            from ..services.student_housing.groups import context, link_selection

            academic = context(request.user, group, request.data, reviewed=False)
            if academic:
                link_selection(group, academic, snapshot)
            elif any(
                x["selection"]["offer_id"] == snapshot["offer_id"]
                and x["selection"]["property_id"] == snapshot["property_id"]
                for x in group.shortlist
            ):
                raise RentalConflict("This accommodation is already shortlisted.")
            else:
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
            from ..services.student_housing.groups import shortlist_decision

            academic, decision = shortlist_decision(
                request.user, group, request.data, item
            )
            if action == "remove_shortlist":
                if academic:
                    item["academic_plan_ids"].remove(str(academic.id))
                    item["revision"] += 1
                else:
                    if item.get("academic_plan_ids") or item.get("academic_decisions"):
                        raise RentalConflict(
                            "Academic history is retained. Remove the accommodation from the relevant plan instead.",
                            code="academic_history_retained",
                        )
                    group.shortlist.remove(item)
                    group.proposals = [
                        x
                        for x in group.proposals
                        if x["offer_id"] != item["selection"]["offer_id"]
                    ]
                    for process in group.processes.exclude(
                        status__in=["withdrawn", "expired", "rejected", "completed"]
                    ):
                        if (
                            process.selection["offer_id"]
                            == item["selection"]["offer_id"]
                        ):
                            invalidate_process(process, "accommodation_removed")
            elif action == "vote":
                choice = request.data.get(
                    "vote",
                    "interested" if request.data.get("consent") is True else "abstain",
                )
                if choice not in {"interested", "maybe", "not_suitable", "abstain"}:
                    raise ValidationError(
                        {"vote": "Choose interested, maybe, not_suitable, or abstain."}
                    )
                votes = decision.setdefault(
                    "votes_by_user",
                    {x: "interested" for x in decision.get("voter_ids", [])},
                )
                if choice == "abstain":
                    votes.pop(actor_id, None)
                else:
                    votes[actor_id] = choice
                decision["voter_ids"] = sorted(
                    x for x, value in votes.items() if value == "interested"
                )
                item["revision"] += 1
            else:
                decision["comments"].append(
                    {
                        "user_id": actor_id,
                        "group_revision": group.revision,
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
            if item.get("academic_plan_id"):
                from ..services.student_housing.groups import context, participant_ids

                academic = context(request.user, group, item)
                if actor_id not in participant_ids(academic):
                    raise PermissionDenied(
                        "Only an intended academic participant may approve their contribution."
                    )
            consent = set(item["approved_by"])
            (
                consent.add(actor_id)
                if request.data.get("consent") is True
                else consent.discard(actor_id)
            )
            item["approved_by"] = sorted(consent)
            item["revision"] += 1
            if request.data.get("consent") is not True:
                for process in group.processes.filter(
                    kind="application", academic_plan__id=item.get("academic_plan_id")
                ).exclude(status__in=["withdrawn", "expired", "rejected", "completed"]):
                    invalidate_process(process, "costs_changed")
        elif action in {"request_visit", "apply"}:
            _submit_process(request, group, action)
        else:
            kind = "visit" if "visit" in action else "application"
            require_planning(
                request.user,
                "group_visits" if kind == "visit" else "group_applications",
            )
            item = get_object_or_404(
                group.processes,
                id=request.data.get("item_id"),
                kind=kind,
            )
            from core_apps.properties.models import Property

            # Listing changes lock the physical property before the process.
            Property.objects.select_for_update().get(pk=item.property_id)
            item = group.processes.select_for_update().get(pk=item.pk)
            check_revision(item.revision, request.data.get("item_revision"))
            check_revision(group.roster_revision, item.roster_revision)
            if action not in process_payload(item, request.user)["allowed_actions"]:
                raise PermissionDenied("This process consent action is unavailable.")
            if action.startswith("withdraw"):
                invalidate_process(item, "consent_withdrawn")
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
        from core_apps.chat.services.group_provisioning import roster_changed

        if action in {"leave", "remove_member", "transfer_admin"}:
            roster_changed(
                group,
                actor=request.user,
                subject=target.user,
                kind={
                    "leave": "member_left",
                    "remove_member": "member_removed",
                    "transfer_admin": "admin_transferred",
                }[action],
            )
        elif action == "edit":
            from core_apps.chat.services.group_provisioning import provision_group
            from core_apps.chat.services.group_events import record_event

            record_event(
                provision_group(group), "conversation.updated", actor=request.user
            )
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
