"""Planning group views: dispatch process."""

import uuid
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.properties.services.visit import PropertyVisitService
from ..services.commands import money_minor
from ..services.planning import (
    check_revision,
    civil_date,
    display_name,
    offer_money,
    selection,
)
from ..services.rental_phase2 import RentalConflict
from .process_payload import active_ids, invalidate_process


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
    from ..services.student_housing.groups import context, participant_ids

    academic = context(request.user, group, {**request.data, **raw})
    members = participant_ids(academic) if academic else active_ids(group)
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
    if previous and previous.get("academic_plan_id") != (
        str(academic.id) if academic else None
    ):
        raise ValidationError(
            {"proposal": "A cost decision cannot move to a different academic period."}
        )
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
        "academic_plan_id": str(academic.id) if academic else None,
        "academic_revision": academic.requirements_revision if academic else None,
    }
    if academic and (
        str(start) != str(academic.starts_on)
        or str(end) != str(academic.ends_on_exclusive)
    ):
        raise ValidationError(
            {"start_on": "The cost proposal must use the reviewed academic dates."}
        )
    if previous:
        group.proposals[group.proposals.index(previous)] = value
    else:
        group.proposals.append(value)
    for process in group.processes.filter(
        kind="application", academic_plan=academic
    ).exclude(status__in=["withdrawn", "expired", "rejected", "completed"]):
        invalidate_process(process, "costs_changed")


def _dispatch_process(request, group, item):
    from ..services.student_housing.groups import process_current

    if not process_current(item):
        raise RentalConflict(
            "Review changed academic requirements before proceeding.",
            code="source_changed",
        )
    prop, snapshot = selection(request, item.selection)
    if item.kind == "visit":
        item.visit = PropertyVisitService.create_visit(
            item.initiated_by,
            prop,
            {
                "offer_id": snapshot["offer_id"],
                "expected_offer_revision": snapshot["offer_revision"],
                "note": item.proposal_snapshot.get("visit_note", ""),
            },
            group=group,
        )
    else:
        proposal = next(
            (
                x
                for x in reversed(group.proposals)
                if x["offer_id"] == snapshot["offer_id"]
                and x["roster_revision"] == group.roster_revision
                and set(x["approved_by"]) == set(item.participant_ids)
                and x.get("academic_plan_id")
                == (str(item.academic_plan.id) if item.academic_plan_id else None)
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
            if end < start + relativedelta(months=months) or (
                not item.academic_plan_id
                and start + relativedelta(months=agreed_months) != end
            ):
                raise ValidationError(
                    {
                        "end_on": "Use a period meeting the offer's minimum monthly term. Ordinary applications require whole calendar months."
                    }
                )
            months = agreed_months
        item.proposal_snapshot = {
            **proposal,
            "participant_ids": list(item.participant_ids),
            "participant_names": {
                str(m.user.id): display_name(m.user)
                for m in group.memberships.filter(
                    status="active", user__id__in=item.participant_ids
                ).select_related("user")
            },
        }
        # An approved group application is not an individual tenancy interest.
        item.status = "under_review"
    if item.kind == "visit":
        item.status = "submitted"
    item.save()
    if item.visit_id:
        from core_apps.properties.services.viewing_commands import notify
        # Booking precedes the process-to-visit link. Now include every approved
        # attendee; the same key preserves the already-created owner receipt.
        notify(item.visit, "requested")
