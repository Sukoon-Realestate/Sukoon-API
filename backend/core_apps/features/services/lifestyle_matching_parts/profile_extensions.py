"""Lifestyle matching: profile extensions."""

from datetime import time
from rest_framework.exceptions import ValidationError


UNKNOWN = {
    None,
    "unspecified",
    "preferNotToAnswer",
    "noPreference",
    "flexible",
    "variable",
}


def profile_extensions(data, dimensions):
    importance = data.get("importance", {})
    reasons = data.get("reason_categories", [])
    details = data.get("details", {})
    context = data.get("search_context", {})
    if (
        not isinstance(importance, dict)
        or set(importance) - dimensions
        or any(
            not isinstance(x, str) or x not in {"flexible", "important", "deal_breaker"}
            for x in importance.values()
        )
    ):
        raise ValidationError(
            {"importance": "Choose flexible, important, or deal_breaker per topic."}
        )
    if not isinstance(reasons, list) or any(
        not isinstance(x, str) or x not in dimensions for x in reasons
    ):
        raise ValidationError(
            {"reason_categories": "Select permitted explanation topics."}
        )
    extra_text = {
        "work_calls",
        "guests_notice",
        "guests_overnight",
        "pet_type",
        "pet_count",
        "cleaning_frequency",
        "shared_chores",
        "shared_spaces",
    }
    allowed = {
        "sleep_start",
        "sleep_end",
        "quiet_start",
        "quiet_end",
        "variable_schedule",
        "notes",
    } | extra_text
    if not isinstance(details, dict) or set(details) - allowed:
        raise ValidationError({"details": "Unsupported lifestyle detail."})
    for key in ("sleep_start", "sleep_end", "quiet_start", "quiet_end"):
        if details.get(key):
            try:
                if not isinstance(details[key], str) or len(details[key]) != 5:
                    raise ValueError
                time.fromisoformat(details[key])
            except ValueError:
                raise ValidationError({key: "Use HH:MM. Windows may cross midnight."})
    for prefix in ("sleep", "quiet"):
        if bool(details.get(prefix + "_start")) != bool(details.get(prefix + "_end")):
            raise ValidationError({"details": "Supply both ends of a time window."})
    if (
        "variable_schedule" in details
        and type(details["variable_schedule"]) is not bool
    ):
        raise ValidationError({"variable_schedule": "Use a boolean."})
    if (
        not isinstance(details.get("notes", ""), str)
        or len(details.get("notes", "")) > 500
    ):
        raise ValidationError({"notes": "Use at most 500 characters."})
    if any(
        not isinstance(details.get(key, ""), str) or len(details.get(key, "")) > 300
        for key in extra_text
    ):
        raise ValidationError(
            {"details": "Use optional text of at most 300 characters per topic."}
        )
    if details.get("pet_count") and (
        not details["pet_count"].isdigit() or int(details["pet_count"]) > 20
    ):
        raise ValidationError({"pet_count": "Use a number from zero to twenty."})
    if not isinstance(context, dict):
        raise ValidationError({"search_context": "Supply supported housing criteria."})
    if context:
        from ..planning import criteria

        context = criteria(context)
    return {
        "importance": importance,
        "reason_categories": sorted(set(reasons)),
        "details": details,
        "search_context": context,
    }


def match_facts(viewer, candidate, dimensions):
    agreements, differences, incomplete = [], [], []
    hard_conflict = False
    agreement_weight, difference_weight = 0, 0
    if viewer is None:
        return False, 0, 0, []
    visible = set(viewer.reason_categories) & set(candidate.reason_categories)
    # Explicit comparable housing constraints cannot silently match different
    # cities, periods or non-overlapping budget ranges.
    left, right = viewer.search_context, candidate.search_context
    if left and right:
        if left.get("city_id") != right.get("city_id"):
            return True, 0, 0, []
        if left.get("price_period") == right.get("price_period"):
            low = max(
                (x.get("budget_min") or {}).get("amount_minor", 0)
                for x in (left, right)
            )
            high = min(
                (x.get("budget_max") or {}).get("amount_minor", float("inf"))
                for x in (left, right)
            )
            if low > high:
                return True, 0, 0, []
    for topic in dimensions:
        outcomes = []
        for source, target in ((viewer, candidate), (candidate, viewer)):
            preference, answer = source.preferences.get(topic), target.habits.get(topic)
            if preference in UNKNOWN or answer in UNKNOWN:
                outcomes.append("unknown")
                continue
            agrees = preference == answer
            if topic == "smoking":
                exposure = {
                    "no": 0,
                    "outdoors": 1,
                    "sometimes": 1,
                    "indoors": 2,
                    "yes": 2,
                }
                agrees = exposure.get(answer, 3) <= exposure.get(preference, -1)
            elif topic == "workFromHome":
                canonical = {"never": "no", "someDays": "sometimes", "mostDays": "yes"}
                agrees = canonical.get(preference, preference) == canonical.get(
                    answer, answer
                )
            outcomes.append("agreement" if agrees else "discussion")
            weight = (
                2
                if source.importance.get(topic) in {"important", "deal_breaker"}
                else 1
            )
            if agrees:
                agreement_weight += weight
            else:
                difference_weight += weight
            if not agrees and source.importance.get(topic) == "deal_breaker":
                hard_conflict = True
        if "discussion" in outcomes:
            differences.append(topic)
        elif outcomes == ["agreement", "agreement"]:
            agreements.append(topic)
        else:
            incomplete.append(topic)
    facts = [
        {"category": topic, "kind": kind}
        for kind, topics in (
            ("agreement", agreements),
            ("discussion", differences),
            ("unknown", incomplete),
        )
        for topic in topics
        if topic in visible
    ]
    return hard_conflict, agreement_weight, difference_weight, facts
