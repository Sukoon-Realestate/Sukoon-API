"""Reviewed public configuration, optional disclosure, amendments and canonical handoffs."""

from datetime import timedelta
from types import SimpleNamespace
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ...living_lab_models import LivingPreferenceDisclosure
from ..planning import check_revision, require_planning, selection
from ..rental_phase2 import RentalConflict
from . import policies
from .commands import fields, require_action, create
from .solver import canonical_inventory, require_run_current
from .retention import scrub_disclosure_receipts
from .access import roster_current

SCENARIOS = {
    "amendment",
    "departure",
    "new_member",
    "work_shift",
    "exam_period",
    "quote_change",
    "room_unavailable",
    "expense_change",
}


def configure(request, lab):
    require_action(request.user, lab, "configure")
    fields(request.data, {"allocation_policy", "household_plan"})
    people = policies.participants(lab)
    lab.allocation_policy = policies.allocation(
        request.data.get("allocation_policy", {}), people
    )
    lab.household_plan = policies.household(
        request.data.get("household_plan", {}), people
    )
    _, _, rent, deposit, _ = canonical_inventory(request, lab)
    policies.shares(rent, people, lab.allocation_policy, "rent")
    policies.shares(deposit, people, lab.allocation_policy, "deposit")
    lab.public_revision += 1
    lab.input_revision += 1
    lab.status = "collecting_inputs"
    lab.disclosures.filter(revoked_at__isnull=True).update(
        values={}, revoked_at=timezone.now()
    )
    scrub_disclosure_receipts(lab)


def disclose(request, lab):
    require_action(request.user, lab, "disclose")
    fields(
        request.data, {"fields", "requirement_revision", "public_revision", "consent"}
    )
    row = lab.requirements.filter(user=request.user, status="provided").first()
    if not row:
        raise ValidationError(
            "Provide your own current inputs before choosing disclosure."
        )
    check_revision(row.revision, request.data.get("requirement_revision"))
    check_revision(lab.public_revision, request.data.get("public_revision"))
    allowed = {"required_room_id", "preferred_room_id", "quiet_windows"}
    chosen = request.data.get("fields", [])
    if (
        not isinstance(chosen, list)
        or any(not isinstance(key, str) or key not in allowed for key in chosen)
        or len(chosen) != len(set(chosen))
    ):
        raise ValidationError(
            "Only your selected room preferences and quiet windows may be disclosed."
        )
    if chosen and request.data.get("consent") is not True:
        raise ValidationError("Personally approve this exact disclosure preview.")
    scrub_disclosure_receipts(lab, [request.user.id])
    LivingPreferenceDisclosure.objects.update_or_create(
        lab=lab,
        user=request.user,
        defaults={
            "requirement_revision": row.revision,
            "public_revision": lab.public_revision,
            "fields": chosen,
            "values": {
                key: row.private_values.get(key, [] if key == "quiet_windows" else "")
                for key in chosen
            },
            "revoked_at": None if chosen else timezone.now(),
        },
    )


def child_lab(request, parent):
    require_action(request.user, parent, "scenario")
    fields(
        request.data,
        {
            "kind",
            "expected_group_revision",
            "agreement_id",
            "departing_user_id",
            "unavailable_room_ids",
            "expense_minor",
            "selection",
            "starts_on",
            "ends_on_exclusive",
        },
    )
    check_revision(parent.group.revision, request.data.get("expected_group_revision"))
    kind = request.data.get("kind")
    if kind not in SCENARIOS:
        raise ValidationError("Choose a documented household change scenario.")
    same_roster = roster_current(parent)
    agreement_id = request.data.get("agreement_id")
    agreement = (
        parent.agreements.filter(id=agreement_id).first() if agreement_id else None
    )
    if agreement_id and not agreement:
        raise ValidationError("Choose an arrangement belonging to this lab.")
    scenario = {
        "kind": kind,
        "policy_version": policies.VERSION,
        "counterfactual": kind in {"departure", "room_unavailable", "expense_change"},
        "obligations_unchanged": True,
    }
    members = {
        str(row.user.id)
        for row in parent.group.memberships.filter(status="active").select_related(
            "user"
        )
    }
    if kind == "departure":
        actor = request.data.get("departing_user_id")
        if actor not in members:
            raise ValidationError(
                "Choose a current participant for the departure assumption."
            )
        scenario["departing_user_id"] = actor
        from ..planning import display_name

        scenario["departing_user_name"] = display_name(
            parent.group.memberships.select_related("user")
            .get(user__id=actor, status="active")
            .user
        )
    # A changed owner quote is accepted only as a fresh canonical selection,
    # reviewed by this coordinator. No hypothetical rent amount is accepted.
    if kind == "quote_change":
        _, current = selection(request, request.data.get("selection"))
        if (
            current["property_id"] != parent.selection["property_id"]
            or current["offer_id"] != parent.selection["offer_id"]
        ):
            raise ValidationError(
                "A quote-change scenario must use the same canonical offer."
            )
        item = next(
            (
                item
                for item in parent.group.shortlist
                if item["id"] == str(parent.shortlist_id)
            ),
            None,
        )
        if not item:
            raise ValidationError(
                "Restore the selected offer in the canonical shortlist first."
            )
        item["selection"], item["revision"] = current, item.get("revision", 0) + 1
        from ...planning_group_views_parts.process_payload import invalidate_process

        for process in parent.group.processes.exclude(
            status__in=["withdrawn", "expired", "rejected", "completed"]
        ):
            if process.selection.get("offer_id") == current["offer_id"]:
                invalidate_process(process)
        parent.group.revision += 1
        parent.group.save(update_fields=["shortlist", "revision", "updated_at"])
    data = {
        "expected_group_revision": parent.group.revision,
        "shortlist_id": str(parent.shortlist_id),
        "title": parent.title if same_roster else parent.group.name,
        "starts_on": request.data.get("starts_on", str(parent.starts_on)),
        "ends_on_exclusive": request.data.get(
            "ends_on_exclusive", str(parent.ends_on_exclusive)
        ),
        "house_rules": (
            parent.house_rules if same_roster and kind != "new_member" else []
        ),
    }
    child = create(SimpleNamespace(user=request.user, data=data), parent.group)
    child.parent_lab, child.parent_agreement, child.scenario = (
        parent,
        agreement,
        scenario,
    )
    # Never copy another person's private input or consent to a new purpose/scope.
    # A new member receives only the newly reviewed canonical offer, not old terms.
    if same_roster and kind != "new_member":
        child.household_plan = parent.household_plan
        child.allocation_policy = parent.allocation_policy
    if kind == "departure":
        child.allocation_policy = {"kind": "equal", "version": policies.VERSION}
        child.household_plan = {
            **child.household_plan,
            "chores": [
                v
                for v in child.household_plan.get("chores", [])
                if v["user_id"] != scenario["departing_user_id"]
            ],
        }
    if kind == "room_unavailable":
        _, rooms, _, _, _ = canonical_inventory(request, child)
        identifiers = request.data.get("unavailable_room_ids", [])
        if (
            not isinstance(identifiers, list)
            or not identifiers
            or any(v not in {room["id"] for room in rooms} for v in identifiers)
        ):
            raise ValidationError(
                "Choose current canonical rooms for the vacancy assumption."
            )
        child.scenario["unavailable_room_ids"] = sorted(set(identifiers))
        child.scenario["unavailable_room_names"] = [
            room["name"] for room in rooms if room["id"] in identifiers
        ]
    if kind == "expense_change":
        expense = request.data.get("expense_minor")
        child.household_plan = policies.household(
            {**child.household_plan, "expense_minor": expense},
            policies.participants(child),
        )
    child.save()
    return child


def current_agreement(request, lab, action):
    require_action(request.user, lab, action)
    check_revision(lab.group.revision, request.data.get("expected_group_revision"))
    _, rooms, _, _, _ = canonical_inventory(request, lab)
    agreement = lab.agreements.filter(
        id=request.data.get("agreement_id"), run__input_revision=lab.input_revision
    ).first()
    if not agreement:
        raise ValidationError("Choose the current unanimously accepted arrangement.")
    require_run_current(agreement.run, lab, rooms)
    if lab.scenario.get("counterfactual"):
        raise ValidationError(
            "Counterfactual arrangements cannot authorize a rental handoff."
        )
    return agreement


def prepare_application(request, lab):
    fields(request.data, {"expected_group_revision", "agreement_id"})
    agreement = current_agreement(request, lab, "prepare_application")
    required = {
        share["user_id"]: share["rent_minor"] for share in agreement.snapshot["shares"]
    }
    proposals = [
        p
        for p in lab.group.proposals
        if p["offer_id"] == lab.selection["offer_id"]
        and set(p["approved_by"]) == set(required)
    ]
    proposal = proposals[-1] if proposals else None
    if (
        not proposal
        or proposal["id"] != str(lab.handoff_proposal_id)
        or proposal["contributions"] != required
        or proposal["offer_revision"] != lab.selection["offer_revision"]
        or proposal["start_on"] != str(lab.starts_on)
        or proposal["end_on"] != str(lab.ends_on_exclusive)
    ):
        raise RentalConflict(
            "Each participant must separately approve this exact canonical cost proposal.",
            code="consent_required",
        )
    from ...planning_group_views_parts.invitation_from_token import _submit_process

    _submit_process(
        SimpleNamespace(
            user=request.user,
            data={
                "participant_ids": sorted(required),
                "selection": lab.selection,
                "consent": False,
            },
        ),
        lab.group,
        "apply",
    )
    lab.handoff_application_id = (
        lab.group.processes.filter(kind="application").latest("created_at").id
    )
    lab.group.revision += 1
    lab.group.save(update_fields=["revision", "updated_at"])


def prepare_tender(request, lab):
    fields(
        request.data,
        {
            "expected_group_revision",
            "agreement_id",
            "request_id",
            "request_revision",
            "closes_at",
        },
    )
    agreement = current_agreement(request, lab, "prepare_tender")
    require_planning(request.user, "collective_tender_planning")
    from ..housing_tenders.commands import create as create_tender

    tender = create_tender(
        request.user,
        {
            "group_id": str(lab.group.id),
            "roster_revision": lab.group.roster_revision,
            "request_id": request.data.get("request_id"),
            "request_revision": request.data.get("request_revision"),
            "title": lab.title,
            "closes_at": request.data.get("closes_at"),
            "execution_mode": "independent_participants",
        },
    )
    tender.source_context = {
        "kind": "living_lab_agreement",
        "lab_id": str(lab.id),
        "agreement_id": str(agreement.id),
        "snapshot": agreement.snapshot,
        "planning_only": True,
    }
    tender.save(update_fields=["source_context", "updated_at"])
    lab.handoff_tender_id = tender.id
