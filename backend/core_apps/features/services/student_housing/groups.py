"""Optional academic scope for the existing group decisions and processes."""

from rest_framework.exceptions import ValidationError
from ..planning import check_revision, require_planning
from ..rental_phase2 import RentalConflict
from .access import plan_for
from .plans import blockers
from .publication import preview


def context(user, group, data, *, reviewed=True):
    identifier = data.get("academic_plan_id")
    if not identifier:
        return None
    require_planning(user, "student_planning")
    plan = plan_for(user, identifier, lock=True)
    if plan.group_id != group.pk:
        raise ValidationError(
            {"academic_plan_id": "The plan must belong to this canonical group."}
        )
    check_revision(plan.requirements_revision, data.get("academic_revision"))
    if plan.status != "planning":
        raise RentalConflict("This academic period is complete.", code="plan_completed")
    if reviewed and blockers(plan):
        raise RentalConflict(
            "The academic participants must review the current requirements.",
            code="consent_required",
        )
    return plan


def participant_ids(plan):
    return sorted(
        str(row.user.id)
        for row in plan.participants.exclude(status="withdrawn").select_related("user")
    )


def shortlist_decision(user, group, data, item):
    """Scope the existing vote/comment commands; never copy earlier period votes."""
    from rest_framework.exceptions import PermissionDenied

    plan = context(user, group, data, reviewed=False)
    if not plan:
        return None, item
    if plan.status != "planning" or plan.roster_revision != group.roster_revision:
        raise RentalConflict(
            "Refresh the current academic participants.", code="roster_changed"
        )
    if str(plan.id) not in item.get("academic_plan_ids", []):
        raise ValidationError({"item_id": "Choose accommodation linked to this plan."})
    if data["action"] != "remove_shortlist" and str(user.id) not in participant_ids(
        plan
    ):
        raise PermissionDenied(
            "Only intended participants can decide for this academic plan."
        )
    decisions = item.setdefault("academic_decisions", {})
    value = decisions.setdefault(
        f"{plan.id}:{plan.requirements_revision}",
        {
            "plan_id": str(plan.id),
            "academic_revision": plan.requirements_revision,
            "roster_revision": group.roster_revision,
            "participant_ids": participant_ids(plan),
            "group_revision": group.revision,
            "votes_by_user": {},
            "comments": [],
        },
    )
    return plan, value


def shortlist_decision_payloads(group, user, item):
    from .access import plans_for

    if not item.get("academic_decisions"):
        return []
    member = group.memberships.get(user=user, status="active")
    plans = {str(plan.id): plan for plan in plans_for(user).filter(group=group)}
    result = []
    for value in item.get("academic_decisions", {}).values():
        plan = plans.get(value["plan_id"])
        if not plan or member.joined_revision > value.get("group_revision", 0):
            continue
        voters = set(value["participant_ids"])
        votes = {
            actor: choice
            for actor, choice in value["votes_by_user"].items()
            if actor in voters
        }
        counts = {
            choice: list(votes.values()).count(choice)
            for choice in ("interested", "maybe", "not_suitable")
        }
        result.append(
            {
                "plan_id": str(plan.id),
                "academic_revision": value["academic_revision"],
                "current": plan.status == "planning"
                and str(plan.id) in item.get("academic_plan_ids", [])
                and plan.requirements_revision == value["academic_revision"]
                and plan.roster_revision
                == group.roster_revision
                == value["roster_revision"],
                "vote_counts": counts,
                "my_vote": votes.get(str(user.id), ""),
                "votes": counts["interested"],
                "abstentions": len(voters - votes.keys()),
                "comments": [comment["text"] for comment in value["comments"]],
            }
        )
    return result


def process_current(process):
    if not process.academic_plan_id:
        return True
    if (
        process.academic_plan.requirements_revision != process.academic_revision
        or blockers(process.academic_plan)
    ):
        return False
    source_id = process.academic_snapshot.get("source_housing_offer_id")
    if source_id:
        from ...planning_models import HousingOffer
        from ...planning_housing_views_parts.housing_request_action import offer_status

        source = HousingOffer.objects.filter(id=source_id).first()
        return bool(
            source
            and source.revision
            == process.academic_snapshot.get("source_housing_offer_revision")
            and offer_status(source, existing_process=True) in {"sent", "viewed"}
        )
    return True


def link_selection(group, plan, selection, *, source=None):
    """Reuse one canonical shortlist item across periods without rewriting decisions."""
    import uuid

    item = next(
        (
            row
            for row in group.shortlist
            if row["selection"]["property_id"] == selection["property_id"]
            and row["selection"]["offer_id"] == selection["offer_id"]
        ),
        None,
    )
    if item is None:
        item = {
            "id": str(uuid.uuid4()),
            "revision": 1,
            "selection": selection,
            "comments": [],
            "voter_ids": [],
        }
        group.shortlist.append(item)
    elif item["selection"].get("offer_revision") != selection.get("offer_revision"):
        raise RentalConflict(
            "Review the changed offer in the existing shortlist.", code="offer_changed"
        )
    identifiers = item.setdefault("academic_plan_ids", [])
    if str(plan.id) not in identifiers:
        identifiers.append(str(plan.id))
        item["revision"] += 1
    if source:
        item.setdefault("academic_sources", {})[str(plan.id)] = source
    return item


def source_snapshot(user, group, plan, selection):
    item = next(
        (
            row
            for row in group.shortlist
            if row["selection"]["property_id"] == selection["property_id"]
            and row["selection"]["offer_id"] == selection["offer_id"]
        ),
        None,
    )
    source = (item or {}).get("academic_sources", {}).get(str(plan.id))
    if not source:
        return {}
    from ...planning_housing_views_parts.housing_request_action import (
        get_offer,
        offer_status,
    )

    response = get_offer(user, source["housing_offer_id"], lock=True)
    if (
        response.revision != source["housing_offer_revision"]
        or offer_status(response) not in {"sent", "viewed"}
        or response.request.academic_revision != plan.requirements_revision
    ):
        raise RentalConflict(
            "Review the changed source housing response.", code="source_changed"
        )
    return {
        "source_housing_offer_id": str(response.id),
        "source_housing_offer_revision": response.revision,
        "student_policy": response.student_policy_snapshot,
    }


def bind_housing_response(user, group, data):
    """Bind the source atomically with a real group action, never on viewing a card."""
    identifier = data.get("source_housing_offer_id")
    if not identifier:
        return
    from ...planning_housing_views_parts.housing_request_action import (
        get_offer,
        offer_status,
    )
    from ...planning_models import HousingRequest

    plan = context(user, group, data)
    if not plan:
        raise ValidationError({"academic_plan_id": "Choose the source academic plan."})
    response = get_offer(user, identifier)
    HousingRequest.objects.select_for_update().get(pk=response.request_id)
    response = get_offer(user, identifier, lock=True)
    check_revision(response.revision, data.get("source_housing_offer_revision"))
    supplied = data.get("selection") or {}
    if (
        response.request.academic_plan_id != plan.pk
        or offer_status(response) not in {"sent", "viewed"}
        or any(
            str(response.selection.get(key)) != str(supplied.get(key))
            for key in ("property_id", "offer_id", "offer_revision")
        )
    ):
        raise RentalConflict(
            "Review the changed source housing response.", code="source_changed"
        )
    link_selection(
        group,
        plan,
        response.selection,
        source={
            "housing_offer_id": str(response.id),
            "housing_offer_revision": response.revision,
        },
    )
