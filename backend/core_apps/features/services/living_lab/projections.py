from django.utils import timezone
from rest_framework.exceptions import APIException
from .access import lab_actions, roster_current
from .solver import canonical_inventory, require_run_current
from .policies import policy_payload
from ..planning import display_name


def private_payload(lab, user):
    row = lab.requirements.filter(user=user).first()
    return {
        "id": str(lab.id),
        "revision": lab.revision,
        "requirement_revision": row.revision if row else 0,
        "public_revision": lab.public_revision,
        "reviewed_public_revision": row.public_revision if row else 0,
        "status": row.status if row else "omitted",
        "purpose_version": row.purpose_version if row else "",
        "values": row.private_values if row else {},
    }


def run_payload(run, lab, user, *, source_current=True):
    current = (
        source_current
        and run.input_revision == lab.input_revision
        and roster_current(lab)
    )
    own = lab.requirements.filter(user=user, status="provided").first()
    result = {
        "id": str(run.id),
        "input_revision": run.input_revision,
        "outcome": run.status if current else "stale",
        "explanation_code": run.explanation_code,
        "policy_version": run.policy_version,
        "created_at": run.created_at.isoformat(),
        "candidates": [],
        "current": current,
    }
    for candidate in run.candidates:
        response = run.responses.filter(user=user, candidate_id=candidate["id"]).first()
        share = next(
            (row for row in candidate["shares"] if row["user_id"] == str(user.id)), None
        )
        preferred = own.private_values.get("preferred_room_id") if own else ""
        result["candidates"].append(
            {
                **candidate,
                "my_response": response.decision if response else "pending",
                "my_preference_difference": bool(
                    preferred and share and preferred != share["room_id"]
                ),
                # Never reveal which other participant declined or their reason.
                "all_accepted": run.lab.agreements.filter(
                    run=run, candidate_id=candidate["id"]
                ).exists(),
            }
        )
    return result


def lab_payload(lab, user, *, detail=True):
    current = roster_current(lab)
    latest = lab.runs.order_by("-created_at").first()
    try:
        _, rooms, _, _, _ = canonical_inventory(None, lab, lock=False)
        if latest and latest.input_revision == lab.input_revision:
            require_run_current(latest, lab, rooms)
    except APIException:
        current = False
    status = (
        "expired"
        if lab.expires_at <= timezone.now()
        else (lab.status if current else "needs_revision")
    )
    own = lab.requirements.filter(user=user).first()
    value = {
        "id": str(lab.id),
        "revision": lab.revision,
        "input_revision": lab.input_revision,
        "public_revision": lab.public_revision,
        "group_id": str(lab.group.id),
        "group_revision": lab.group.revision,
        "roster_revision": lab.roster_revision,
        "title": lab.title,
        "status": status,
        "selection": lab.selection,
        "starts_on": str(lab.starts_on),
        "ends_on_exclusive": str(lab.ends_on_exclusive),
        "house_rules": lab.house_rules,
        "allocation_policy": lab.allocation_policy,
        "household_plan": lab.household_plan,
        "scenario": lab.scenario,
        "policy": policy_payload(),
        "participant_count": len(lab.participant_periods),
        "ready_count": (
            lab.requirements.filter(
                status="provided", public_revision=lab.public_revision
            ).count()
            if current
            else 0
        ),
        "my_input_status": own.status if own else "omitted",
        "planning_only": True,
        "expires_at": lab.expires_at.isoformat(),
        "allowed_actions": (
            lab_actions(user, lab)
            if current
            else [
                action
                for action in lab_actions(user, lab)
                if action in {"withdraw", "close", "scenario"}
            ]
        ),
        "handoff_proposal_id": (
            str(lab.handoff_proposal_id) if lab.handoff_proposal_id else ""
        ),
        "handoff_application_id": str(lab.handoff_application_id or ""),
        "handoff_tender_id": str(lab.handoff_tender_id or ""),
        "parent_lab_id": str(lab.parent_lab.id) if lab.parent_lab_id else "",
        "purged_at": lab.purged_at.isoformat() if lab.purged_at else "",
    }
    if detail:
        from .notifications import public_history

        value["public_history"] = public_history(lab)
        value["previous_arrangement"] = None
        if lab.parent_agreement_id:
            from .access import lab_for
            from rest_framework.exceptions import NotFound

            try:
                lab_for(user, lab.parent_lab.id)
                value["previous_arrangement"] = lab.parent_agreement.snapshot
            except NotFound:
                pass
        value["participants"] = [
            {"id": str(member.user.id), "name": display_name(member.user)}
            for member in lab.group.memberships.filter(status="active").select_related(
                "user"
            )
        ]
        requirements = {row.user_id: row for row in lab.requirements.all()}
        value["disclosures"] = [
            {
                "user_id": str(row.user.id),
                "user_name": display_name(row.user),
                "fields": row.fields,
                "values": row.values,
            }
            for row in lab.disclosures.filter(revoked_at__isnull=True).select_related(
                "user"
            )
            if current
            and row.public_revision == lab.public_revision
            and row.user_id in requirements
            and row.requirement_revision == requirements[row.user_id].revision
        ]
        value["my_disclosure_fields"] = list(
            lab.disclosures.filter(user=user, revoked_at__isnull=True)
            .values_list("fields", flat=True)
            .first()
            or []
        )
        value["tender_sources"] = []
        if "prepare_tender" in value["allowed_actions"]:
            from ...planning_models import HousingRequest

            value["tender_sources"] = [
                {"id": str(row.id), "revision": row.revision, "title": row.title}
                for row in HousingRequest.objects.filter(
                    user=user, status="published", expires_at__gt=timezone.now()
                ).order_by("-created_at")[:20]
            ]
        value["latest_run"] = (
            run_payload(latest, lab, user, source_current=current) if latest else None
        )
        value["agreements"] = [
            {
                "id": str(row.id),
                "created_at": row.created_at.isoformat(),
                "current": current and row.run.input_revision == lab.input_revision,
                "snapshot": row.snapshot,
            }
            for row in lab.agreements.select_related("run").order_by("-created_at")
        ]
        # These are public canonical room identities, never private preferences.
        from core_apps.properties.models import Property

        prop = Property.objects.filter(id=lab.selection.get("property_id")).first()
        value["current_selection"] = {}
        if prop:
            offer = next(
                (
                    v
                    for v in (prop.rental_inventory or {}).get("offers", [])
                    if str(v.get("id")) == lab.selection.get("offer_id")
                ),
                None,
            )
            if offer:
                try:
                    from ..planning import selection

                    _, value["current_selection"] = selection(
                        None,
                        {
                            "property_id": str(prop.id),
                            "offer_id": offer["id"],
                            "offer_revision": offer["revision"],
                        },
                        lock=False,
                    )
                except APIException:
                    pass
        value["rooms"] = [
            {"id": str(room.get("id", "")), "name": str(room.get("name", ""))}
            for room in ((prop.rental_inventory or {}).get("rooms", []) if prop else [])
            if lab.selection.get("rental_scope") == "entire_property"
            or str(room.get("id")) in lab.selection.get("room_ids", [])
        ]
    return value
