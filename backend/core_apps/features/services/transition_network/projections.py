from django.utils import timezone
from rest_framework.exceptions import APIException
from config.advanced_housing import POLICY_VERSION, execution_available, execution_mode
from .access import intent_actions
from ..planning import money, criteria_payload, enabled_services


def intent_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "source_transition_id": str(item.source_transition.id),
        "revision": item.revision,
        "status": item.status,
        "criteria": criteria_payload(item.criteria),
        "max_deposit": money(item.max_deposit_minor),
        "max_gap_days": item.max_gap_days,
        "turnover_days": item.turnover_days,
        "matching_consent": item.matching_consent,
        "expires_at": item.expires_at.isoformat(),
        "execution_available": execution_enabled(),
        "blocking_reason_codes": (
            [] if execution_enabled() else ["housing_transition_execution_unavailable"]
        ),
        "allowed_actions": (
            intent_actions(item)
            if "housing_transition_planning" in enabled_services()
            else []
        ),
    }


def candidate_stale(item, *, check_expiry=True, check_availability=True):
    if check_expiry and item.expires_at <= timezone.now():
        return True
    from .solver import source_snapshot, validate_cycle

    intents, sources = {}, {}
    for participant in item.participants.select_related(
        "intent__lease__property", "intent__source_transition", "intent__user"
    ):
        intent = participant.intent
        if (
            intent.revision != participant.intent_revision
            or intent.status != "matching"
            or not intent.user.is_active
            or not intent.user.is_verified
            or not intent.matching_consent
            or intent.expires_at <= timezone.now()
        ):
            return True
        try:
            current = source_snapshot(intent)
        except APIException:
            return True
        expected = (item.snapshot.get("source_manifest") or {}).get(
            str(intent.id)
        ) or next(
            (
                leg["source"]
                for leg in item.snapshot["legs"]
                if leg["source"].get("intent_id") == str(intent.id)
            ),
            None,
        )
        if current != expected:
            return True
        intents[str(intent.id)] = intent
        sources[str(intent.id)] = current
    ordered = [intents[leg["intent_id"]] for leg in item.snapshot["legs"]]
    endpoint = item.snapshot.get("endpoint")
    if endpoint:
        from .vacancies import vacancy_snapshot
        from core_apps.properties.models import Property

        try:
            prop = Property.objects.get(id=endpoint["selection"]["property_id"])
            if vacancy_snapshot(prop, endpoint["selection"]["offer_id"]) != endpoint:
                return True
        except (APIException, Property.DoesNotExist):
            return True
    if (
        check_availability
        and validate_cycle(ordered, sources, endpoint=endpoint) is None
    ):
        return True
    return False


def execution_enabled():
    return (
        execution_available() and "housing_transition_execution" in enabled_services()
    )


def candidate_actions(item, stale):
    actions = []
    if not stale and "housing_transition_planning" in enabled_services():
        actions.append("interest")
    if (
        not stale
        and execution_enabled()
        and not item.participants.exclude(decision="interested").exists()
    ):
        actions.append("create_execution")
    return actions


def candidate_payload(item, user):
    own = item.participants.get(user=user)
    leg = next(
        value for value in item.snapshot["legs"] if value["user_id"] == str(user.id)
    )
    stale = candidate_stale(item)
    # Deliberately omit other participants' sources, identities, addresses, bounds,
    # exact costs and response choices. Interest does not create an obligation.
    destination = leg["source"]
    from ...advanced_execution_models import AdvancedExecution

    execution = (
        AdvancedExecution.objects.filter(source_kind="transition", source_id=item.id)
        .order_by("-created_at")
        .first()
    )
    return {
        "id": str(item.id),
        "revision": item.revision,
        "snapshot_digest": item.snapshot_digest,
        "policy_version": POLICY_VERSION,
        "status": "needs_replan" if stale else item.status,
        "result_status": "stale" if stale else item.snapshot["result_status"],
        "participant_count": len(item.snapshot["legs"]),
        "kind": item.snapshot.get("kind", "cycle"),
        "selection": destination["selection"],
        "start_on": leg["start_on"],
        "end_on": leg["end_on"],
        "rent": money(destination["rent_minor"]),
        "deposit": money(destination["deposit_minor"]),
        "gap_days": leg["gap_days"],
        "my_decision": own.decision,
        "expires_at": item.expires_at.isoformat(),
        "source_checked_at": item.created_at.isoformat(),
        "inventory_reserved": False,
        "execution_available": execution_enabled(),
        "execution_id": str(execution.id) if execution else "",
        "provider_mode": execution_mode() if execution_enabled() else "disabled",
        "rent_change": money(
            abs(destination["rent_minor"] - own.intent.lease.rent_amount_minor)
        ),
        "rent_change_direction": (
            "increase"
            if destination["rent_minor"] > own.intent.lease.rent_amount_minor
            else (
                "decrease"
                if destination["rent_minor"] < own.intent.lease.rent_amount_minor
                else "unchanged"
            )
        ),
        "blocking_reason_codes": (
            (
                []
                if execution_enabled()
                else ["housing_transition_execution_unavailable"]
            )
            + (
                []
                if item.snapshot["result_status"] == "feasible"
                else ["physical_release_requires_confirmation"]
            )
        ),
        "allowed_actions": candidate_actions(item, stale),
    }


def run_payload(item):
    stale = (
        item.intent.revision != item.input_revision or item.intent.status != "matching"
    )
    return {
        "id": str(item.id),
        "revision": item.revision,
        "intent_id": str(item.intent.id),
        "status": item.status,
        "result_status": "stale" if stale else item.result_status,
        "searched_count": item.searched_count,
        "pool_limited": item.pool_limited,
        "failure_code": item.failure_code,
        "candidate_count": item.candidates.count(),
        "execution_available": execution_enabled(),
    }
