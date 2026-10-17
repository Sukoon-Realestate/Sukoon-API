from datetime import timedelta
from types import SimpleNamespace

from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from ...living_lab_models import (
    ArrangementResponse,
    LivingLabAuditEvent,
    LivingLabRun,
    PrivateParticipantRequirement,
    SharedArrangementSnapshot,
    SharedLivingLab,
)
from ..planning import check_revision, civil_date, selection, text_field
from ..rental_phase2 import RentalConflict
from .access import lab_actions
from . import policies
from .solver import (
    PURPOSE_VERSION,
    canonical_inventory,
    input_digest,
    require_run_current,
    solve,
)


def fields(data, allowed):
    if not isinstance(data, dict) or set(data) - {
        "request_key",
        "expected_revision",
        *allowed,
    }:
        raise ValidationError(
            "Only documented fields for your own action are accepted."
        )


def create(request, group):
    data = request.data
    fields(
        data,
        {
            "expected_group_revision",
            "shortlist_id",
            "title",
            "starts_on",
            "ends_on_exclusive",
            "house_rules",
        },
    )
    check_revision(group.revision, data.get("expected_group_revision"))
    members = list(
        group.memberships.filter(status="active")
        .select_related("user")
        .order_by("user__id")
    )
    if not 2 <= len(members) <= policies.limit("MAX_PARTICIPANTS", 6):
        raise ValidationError(
            "Use an existing group with at least two people within the configured planning limit."
        )
    if group.living_labs.filter(
        created_at__gte=timezone.now() - timedelta(days=1)
    ).count() >= policies.limit("MAX_LABS_PER_GROUP_DAY", 8):
        raise RentalConflict(
            "The daily group planning limit has been reached.", code="scenario_limit"
        )
    item = next(
        (row for row in group.shortlist if row["id"] == data.get("shortlist_id")), None
    )
    if item is None:
        raise ValidationError(
            {"shortlist_id": "Choose a current canonical shortlist item."}
        )
    # Only copy the public canonical selection. Academic sources, decisions, and
    # prior participant consent are deliberately excluded from this new lab.
    _, snapshot = selection(request, item["selection"])
    start = civil_date(data.get("starts_on"), "starts_on", future=True)
    end = civil_date(data.get("ends_on_exclusive"), "ends_on_exclusive")
    if not 1 <= (end - start).days <= 730:
        raise ValidationError(
            {"ends_on_exclusive": "Choose a period of one to 730 days."}
        )
    rules = data.get("house_rules", [])
    if (
        not isinstance(rules, list)
        or len(rules) > 4
        or any(
            not isinstance(rule, str) or not rule.strip() or len(rule) > 200
            for rule in rules
        )
    ):
        raise ValidationError(
            {"house_rules": "Use at most four short, voluntary household proposals."}
        )
    lab = SharedLivingLab(
        group=group,
        created_by=request.user,
        title=text_field(data, "title", required=True, limit=120),
        access_group_revision=group.revision,
        roster_revision=group.roster_revision,
        participant_periods=[
            {
                "user_id": str(row.user.id),
                "membership_id": str(row.id),
                "period": row.joined_revision,
            }
            for row in members
        ],
        shortlist_id=item["id"],
        selection=snapshot,
        starts_on=start,
        ends_on_exclusive=end,
        house_rules=[rule.strip() for rule in rules],
        expires_at=timezone.now() + timedelta(days=policies.limit("ACTIVE_DAYS", 14)),
    )
    canonical_inventory(request, lab)
    lab.save()
    LivingLabAuditEvent.objects.create(lab=lab, actor=request.user, event="created")
    return lab


def require_action(user, lab, action):
    if action not in lab_actions(user, lab):
        raise PermissionDenied(
            {
                "message": "Refresh the current group, access period, and lab state.",
                "code": "action_unavailable",
            }
        )


def save_requirements(request, lab):
    require_action(request.user, lab, "requirements")
    data = request.data
    fields(
        data,
        {"status", "purpose_version", "purpose_accepted", "values", "public_revision"},
    )
    status = data.get("status")
    if status not in {"provided", "omitted"}:
        raise ValidationError({"status": "Choose provided or omitted."})
    values = data.get("values", {})
    if not isinstance(values, dict):
        raise ValidationError({"values": "Use a private requirements object."})
    if status == "provided":
        check_revision(lab.public_revision, data.get("public_revision", 1))
        if (
            data.get("purpose_accepted") is not True
            or data.get("purpose_version") != PURPOSE_VERSION
        ):
            raise ValidationError(
                {
                    "purpose_accepted": "Personally accept this specific computation purpose."
                }
            )
        allowed = {
            "rent_max_minor",
            "deposit_max_minor",
            "accepted_start_on",
            "accepted_end_on",
            "private_room",
            "required_room_id",
            "preferred_room_id",
        }
        optional = {
            "expense_max_minor",
            "quiet_windows",
            "unavailable_windows",
            "accepted_chore_ids",
        }
        if not allowed.issubset(values) or set(values) - allowed - optional:
            raise ValidationError(
                {"values": "Supply the documented private bounds and room choices."}
            )
        for field in ("rent_max_minor", "deposit_max_minor"):
            if type(values[field]) is not int or not 0 <= values[field] <= 10**12:
                raise ValidationError(
                    {field: "Use a nonnegative integer number of minor units."}
                )
        expense = values.get("expense_max_minor")
        if expense is not None and (
            type(expense) is not int or not 0 <= expense <= 10**12
        ):
            raise ValidationError("Use a nonnegative private shared expense limit.")
        for field in ("quiet_windows", "unavailable_windows"):
            if field in values:
                values[field] = policies.windows(values[field])
        accepted = values.get("accepted_chore_ids", [])
        known = {
            task["id"]
            for task in lab.household_plan.get("chores", [])
            if task["user_id"] == str(request.user.id)
        }
        if (
            not isinstance(accepted, list)
            or any(not isinstance(v, str) or v not in known for v in accepted)
            or len(accepted) != len(set(accepted))
        ):
            raise ValidationError(
                "Personally choose only household tasks proposed for you."
            )
        start = civil_date(values["accepted_start_on"], "accepted_start_on")
        end = civil_date(values["accepted_end_on"], "accepted_end_on")
        if end <= start or type(values["private_room"]) is not bool:
            raise ValidationError(
                {"values": "Use ordered dates and an explicit private-room choice."}
            )
        _, rooms, _, _, _ = canonical_inventory(request, lab)
        allowed_rooms = {"", *(room["id"] for room in rooms)}
        if any(
            type(values[key]) is not str or values[key] not in allowed_rooms
            for key in ("required_room_id", "preferred_room_id")
        ):
            raise ValidationError(
                {"values": "Choose room identities from this exact offer."}
            )
    elif values:
        raise ValidationError(
            {"values": "Omitted inputs must not contain private values."}
        )
    member = lab.group.memberships.get(user=request.user, status="active")
    row, _ = PrivateParticipantRequirement.objects.get_or_create(
        lab=lab,
        user=request.user,
        defaults={
            "membership": member,
            "membership_period": member.joined_revision,
            "revision": 0,
        },
    )
    row.status, row.private_values = status, values
    row.purpose_version = PURPOSE_VERSION if status == "provided" else ""
    row.consented_at = timezone.now() if status == "provided" else None
    row.public_revision = lab.public_revision
    row.revision += 1
    row.save()
    lab.disclosures.filter(user=request.user, revoked_at__isnull=True).update(
        revoked_at=timezone.now(), values={}
    )
    from .retention import scrub_disclosure_receipts

    scrub_disclosure_receipts(lab, [request.user.id])
    lab.runs.exclude(input_digest="").update(input_digest="")
    lab.input_revision += 1
    lab.status = "needs_revision" if lab.runs.exists() else "collecting_inputs"
    return lab


def run(request, lab):
    fields(request.data, set())
    require_action(request.user, lab, "run")
    if lab.runs.count() >= policies.limit(
        "MAX_RUNS_PER_LAB", 6
    ) or LivingLabRun.objects.filter(
        lab__group=lab.group, created_at__gte=timezone.now() - timedelta(days=1)
    ).count() >= policies.limit(
        "MAX_RUNS_PER_GROUP_DAY", 12
    ):
        raise RentalConflict(
            "The bounded group scenario limit has been reached.", code="scenario_limit"
        )
    if lab.runs.filter(input_revision=lab.input_revision).exists():
        raise RentalConflict(
            "This input revision already has a result.",
            code="scenario_already_computed",
        )
    rows = list(lab.requirements.select_related("user").order_by("user__id"))
    try:
        _, rooms, rent, deposit, keys = canonical_inventory(request, lab)
    except APIException:
        outcome, explanation, candidates, examined = "stale", "source_changed", [], 0
        digest = input_digest(lab, rows, [])
    else:
        digest = input_digest(lab, rows, rooms)
        outcome, explanation, candidates, examined = solve(
            lab, rows, rooms, rent, deposit, keys
        )
    LivingLabRun.objects.create(
        lab=lab,
        input_revision=lab.input_revision,
        input_digest=digest,
        status=outcome,
        explanation_code=explanation,
        candidates=candidates,
        examined_assignments=examined,
        policy_version=policies.VERSION,
    )
    lab.status = "proposal_ready" if candidates else "needs_revision"
    return lab


def respond(request, lab):
    fields(request.data, {"run_id", "candidate_id", "input_revision", "decision"})
    require_action(request.user, lab, "respond")
    check_revision(lab.input_revision, request.data.get("input_revision"))
    _, rooms, _, _, _ = canonical_inventory(request, lab)
    result = lab.runs.filter(
        id=request.data.get("run_id"), input_revision=lab.input_revision
    ).first()
    candidate = (
        next(
            (
                row
                for row in result.candidates
                if row["id"] == request.data.get("candidate_id")
            ),
            None,
        )
        if result
        else None
    )
    decision = request.data.get("decision")
    if candidate is None or decision not in {"accept", "reject", "request_revision"}:
        raise ValidationError(
            "Choose a current candidate and your own explicit response."
        )
    require_run_current(result, lab, rooms)
    period = next(
        row["period"]
        for row in lab.participant_periods
        if row["user_id"] == str(request.user.id)
    )
    result.responses.filter(user=request.user).update(decision="request_revision")
    ArrangementResponse.objects.update_or_create(
        run=result,
        candidate_id=candidate["id"],
        user=request.user,
        defaults={"membership_period": period, "decision": decision},
    )
    lab.status = "collecting_responses"
    accepted = set(
        str(value)
        for value in result.responses.filter(
            candidate_id=candidate["id"], decision="accept"
        ).values_list("user__id", flat=True)
    )
    if accepted == {row["user_id"] for row in lab.participant_periods}:
        SharedArrangementSnapshot.objects.get_or_create(
            lab=lab,
            run=result,
            candidate_id=candidate["id"],
            defaults={
                "snapshot": {
                    **candidate,
                    "input_revision": lab.input_revision,
                    "roster_revision": lab.roster_revision,
                    "access_group_revision": lab.access_group_revision,
                    "group_revision": lab.group.revision,
                    "participant_periods": lab.participant_periods,
                    "accepted_by": sorted(accepted),
                    "planning_only": True,
                }
            },
        )
        lab.status = "agreed"
    return lab


def handoff(request, lab):
    fields(request.data, {"expected_group_revision", "agreement_id"})
    require_action(request.user, lab, "prepare_cost_proposal")
    check_revision(lab.group.revision, request.data.get("expected_group_revision"))
    _, rooms, _, _, _ = canonical_inventory(request, lab)
    agreement = lab.agreements.filter(
        id=request.data.get("agreement_id"), run__input_revision=lab.input_revision
    ).first()
    if not agreement:
        raise ValidationError(
            {"agreement_id": "Choose the current unanimously accepted arrangement."}
        )
    require_run_current(agreement.run, lab, rooms)
    if lab.scenario.get("counterfactual"):
        raise ValidationError(
            "Counterfactual arrangements cannot authorize a rental handoff."
        )
    from ...planning_group_views_parts.dispatch_process import _proposal

    shared = agreement.snapshot
    proxy = SimpleNamespace(
        user=request.user,
        data={
            "proposal": {
                "revision": 0,
                "roster_revision": lab.group.roster_revision,
                "offer_id": lab.selection["offer_id"],
                "offer_revision": lab.selection["offer_revision"],
                "total": shared["rent_total"],
                "period": lab.selection["terms"]["price_period"],
                "start_on": str(lab.starts_on),
                "end_on": str(lab.ends_on_exclusive),
                "contributions": {
                    row["user_id"]: row["rent_minor"] for row in shared["shares"]
                },
            }
        },
    )
    _proposal(proxy, lab.group)
    lab.handoff_proposal_id = lab.group.proposals[-1]["id"]
    lab.group.revision += 1
    lab.group.save(update_fields=["proposals", "revision", "updated_at"])
    # Canonical proposal starts with approved_by=[]; lab acceptance never grants financial authority.
    return lab


def change(request, lab, action):
    if action == "requirements":
        save_requirements(request, lab)
    elif action == "run":
        run(request, lab)
    elif action == "respond":
        respond(request, lab)
    elif action == "prepare_cost_proposal":
        handoff(request, lab)
    elif action in {"configure", "disclose", "prepare_application", "prepare_tender"}:
        from .journeys import configure, disclose, prepare_application, prepare_tender

        {
            "configure": configure,
            "disclose": disclose,
            "prepare_application": prepare_application,
            "prepare_tender": prepare_tender,
        }[action](request, lab)
    elif action in {"withdraw", "close"}:
        fields(request.data, set())
        require_action(request.user, lab, action)
        if action == "withdraw":
            lab.requirements.filter(user=request.user).update(
                status="withdrawn",
                private_values={},
                purpose_version="",
                consented_at=None,
            )
            lab.disclosures.filter(user=request.user).update(
                values={}, revoked_at=timezone.now()
            )
            from .retention import scrub_disclosure_receipts

            scrub_disclosure_receipts(lab, [request.user.id])
            lab.runs.exclude(input_digest="").update(input_digest="")
            lab.input_revision += 1
            if lab.status not in {"closed", "expired"}:
                lab.status = "needs_revision"
        else:
            lab.status = "closed"
    else:
        raise ValidationError("This planning action is unsupported.")
    lab.revision += 1
    lab.save()
    LivingLabAuditEvent.objects.create(lab=lab, actor=request.user, event=action)
    return lab
