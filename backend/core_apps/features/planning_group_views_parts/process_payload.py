"""Planning group views: process payload."""

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from ..planning_models import HousingGroup
from ..services.planning import check_revision, criteria, text_field
from ..services.rental_phase2 import RentalConflict


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
    if not member:
        return []
    if group.status != "active":
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


def process_history(item):
    return [
        {
            key: row[key]
            for key in (
                "action",
                "reason_code",
                "at",
                "revision",
                "from_status",
                "to_status",
                "source_revision",
                "listing_changes",
            )
            if key in row
        }
        for row in item.history
    ]


def process_payload(item, user):
    status = item.status
    if item.visit_id and status in {"submitted", "scheduled"}:
        status = {
            "pending": "submitted",
            "confirmed": "accepted",
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
        status
        in {
            "collecting_consent",
            "ready",
            "submitted",
            "scheduled",
            "accepted",
            "under_review",
            "approved_to_proceed",
        }
        and actor_id in item.participant_ids
    ):
        suffix = "visit" if item.kind == "visit" else "application"
        actions = (
            [f"withdraw_{suffix}_consent"]
            if actor_id in item.consented_ids
            else [f"consent_{suffix}"]
        )
    return {
        "academic_plan_id": (
            str(item.academic_plan.id) if item.academic_plan_id else None
        ),
        "academic_revision": item.academic_revision,
        "id": str(item.id),
        "revision": item.revision,
        "roster_revision": item.roster_revision,
        "status": status,
        "selection": item.selection,
        "participant_ids": item.participant_ids,
        "consented_ids": item.consented_ids,
        "qualifying_visit_id": str(item.visit.id) if item.visit_id else "",
        "interest_id": str(item.interest.id) if item.interest_id else "",
        "allowed_actions": actions,
        "proposal_snapshot": item.proposal_snapshot,
        "owner_note": item.owner_note,
        "history": process_history(item),
        "request_note": (
            item.proposal_snapshot.get("visit_note", "") if item.kind == "visit" else ""
        ),
        "joint_contract_supported": False,
        "blocking_reasons": (
            ["Joint contracting is not available; approval does not create a lease."]
            if item.kind == "application" and status == "approved_to_proceed"
            else []
        ),
    }


def _group_values(data):
    if data.get("visibility", "invite_only") not in {"invite_only", "private", "open"}:
        raise ValidationError({"visibility": "Choose private, invite_only, or open."})
    capacity = data.get("capacity")
    if type(capacity) is not int or not 2 <= capacity <= 20:
        raise ValidationError({"capacity": "Use an integer between 2 and 20."})
    return {
        "name": text_field(data, "name", required=True, limit=160),
        "visibility": data.get("visibility", "invite_only"),
        "capacity": capacity,
        "criteria": criteria(data.get("criteria")),
    }


@transaction.atomic
def invalidate_process(
    item, reason_code="consent_or_source_changed", *, source_change=None
):
    from ..planning_models import GroupProcess
    from core_apps.properties.models import PropertyVisit

    GroupProcess.objects.select_for_update().get(pk=item.pk)
    item.refresh_from_db()
    if item.status in {"withdrawn", "expired", "rejected", "completed"}:
        return
    previous_status = item.status
    previous_consents = list(item.consented_ids)
    if item.visit_id:
        item.visit = PropertyVisit.objects.select_for_update().get(pk=item.visit_id)

    def record():
        item.history.append(
            {
                "action": "source_changed",
                "reason_code": reason_code,
                "at": timezone.now().isoformat(),
                "revision": item.revision,
                "from_status": previous_status,
                "to_status": item.status,
                "previous_consented_ids": previous_consents,
                **(source_change or {}),
            }
        )
        item.save()
        from ..services.group_process_events import record_change

        record_change(item, previous_status)

    if item.visit_id and item.visit.participant_decisions.exists():
        # A later membership change cannot erase other attendees' statements or
        # committed invitations. Fresh participant checks still revoke leavers.
        item.status = "completed"
        item.revision += 1
        record()
        return
    if (
        item.visit_id
        and item.visit.status in {"pending", "confirmed"}
        and not item.visit.participant_decisions.exists()
    ):
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
    record()


def invalidate_roster(group):
    group.roster_revision += 1
    for proposal in group.proposals:
        proposal["approved_by"] = []
        proposal["revision"] += 1
    for item in group.processes.exclude(
        status__in=["withdrawn", "expired", "rejected", "completed"]
    ):
        invalidate_process(item, "roster_changed")


def _shortlist_item(group, data):
    item = next((x for x in group.shortlist if x["id"] == data.get("item_id")), None)
    if not item:
        raise ValidationError({"item_id": "Choose a persisted shortlist item."})
    check_revision(item["revision"], data.get("item_revision"))
    return item
