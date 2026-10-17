"""Versioned planning policy. These configurable bounds are product defaults, not legal terms."""

from django.conf import settings
from rest_framework.exceptions import ValidationError

VERSION = "living-arrangements-v2"


def limit(name, default):
    value = getattr(settings, "LIVING_LAB_" + name, default)
    return value if type(value) is int and value > 0 else default


def participants(lab):
    excluded = lab.scenario.get("departing_user_id", "")
    return sorted(
        row["user_id"] for row in lab.participant_periods if row["user_id"] != excluded
    )


def policy_payload():
    return {
        "version": VERSION,
        "max_share_ratio": limit("MAX_SHARE_RATIO", 4),
        "max_runs_per_lab": limit("MAX_RUNS_PER_LAB", 6),
        "max_runs_per_group_day": limit("MAX_RUNS_PER_GROUP_DAY", 12),
        "active_days": limit("ACTIVE_DAYS", 14),
        "private_retention_days": limit("PRIVATE_RETENTION_DAYS", 30),
        "uncommitted_retention_days": limit("UNCOMMITTED_RETENTION_DAYS", 30),
    }


def windows(value, *, dates=False):
    if not isinstance(value, list) or len(value) > 8:
        raise ValidationError("Use at most eight weekly time windows.")
    result = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {
            "weekday",
            "start_minute",
            "end_minute",
        }:
            raise ValidationError(
                "Specify a weekday and start and end minutes for each window."
            )
        day, start, end = (
            item[key] for key in ("weekday", "start_minute", "end_minute")
        )
        if any(type(v) is not int for v in (day, start, end)) or not (
            1 <= day <= 7 and 0 <= start < end <= 1440
        ):
            raise ValidationError(
                "Weekly windows must stay within one day and have ordered times."
            )
        result.append({"weekday": day, "start_minute": start, "end_minute": end})
    return result


def allocation(value, people):
    if not isinstance(value, dict) or set(value) - {
        "kind",
        "weights",
        "rent_shares",
        "deposit_shares",
    }:
        raise ValidationError("Use a documented cost allocation policy.")
    kind = value.get("kind", "equal")
    if kind not in {"equal", "weighted", "negotiated"}:
        raise ValidationError("Choose equal, weighted, or negotiated shares.")
    result = {"kind": kind, "version": VERSION}
    for field in (
        {"weights"}
        if kind == "weighted"
        else {"rent_shares", "deposit_shares"} if kind == "negotiated" else set()
    ):
        entries = value.get(field)
        if (
            not isinstance(entries, dict)
            or set(entries) != set(people)
            or any(type(v) is not int or v < 0 for v in entries.values())
        ):
            raise ValidationError(
                "Every proposed participant needs an explicit integer share or weight."
            )
        if min(entries.values()) <= 0 or max(entries.values()) > min(
            entries.values()
        ) * limit("MAX_SHARE_RATIO", 4):
            # Zero deposits are valid when explicitly zero for everyone.
            if not (field == "deposit_shares" and not any(entries.values())):
                raise ValidationError(
                    "Unequal shares must respect the disclosed maximum ratio."
                )
        result[field] = dict(sorted(entries.items()))
    return result


def household(value, people):
    if not isinstance(value, dict) or set(value) - {
        "quiet_windows",
        "chores",
        "visitor_policy",
        "expense_minor",
    }:
        raise ValidationError("Use the documented household arrangement fields.")
    quiet = windows(value.get("quiet_windows", []))
    chores = value.get("chores", [])
    if not isinstance(chores, list) or len(chores) > 12:
        raise ValidationError("Use at most twelve voluntary household tasks.")
    normalized, identifiers = [], set()
    for item in chores:
        if not isinstance(item, dict) or set(item) != {
            "id",
            "title",
            "user_id",
            "weekday",
            "start_minute",
            "duration_minutes",
        }:
            raise ValidationError(
                "Each household task needs its identity, person, and weekly time."
            )
        task_id, title = item["id"], item["title"]
        day, start, duration = (
            item["weekday"],
            item["start_minute"],
            item["duration_minutes"],
        )
        if (
            not isinstance(task_id, str)
            or not task_id
            or len(task_id) > 40
            or task_id in identifiers
            or not isinstance(title, str)
            or not title.strip()
            or len(title) > 80
            or item["user_id"] not in people
        ):
            raise ValidationError(
                "Use unique household task identities and current participants."
            )
        if any(type(v) is not int for v in (day, start, duration)) or not (
            1 <= day <= 7
            and 0 <= start < 1440
            and 1 <= duration <= 180
            and start + duration <= 1440
        ):
            raise ValidationError("Household task times must fit within a day.")
        identifiers.add(task_id)
        normalized.append({**item, "title": title.strip()})
    visitor = value.get("visitor_policy", "")
    expense = value.get("expense_minor", 0)
    if (
        not isinstance(visitor, str)
        or len(visitor) > 400
        or type(expense) is not int
        or not 0 <= expense <= 10**9
    ):
        raise ValidationError(
            "Use a short visitor proposal and a nonnegative shared expense amount."
        )
    return {
        "quiet_windows": quiet,
        "chores": normalized,
        "visitor_policy": visitor.strip(),
        "expense_minor": expense,
    }


def shares(total, people, policy, component):
    kind = policy.get("kind", "equal")
    if kind == "negotiated" and component != "expense":
        values = policy.get(component + "_shares", {})
        if set(values) != set(people) or sum(values.values()) != total:
            raise ValidationError(
                "Negotiated shares must sum exactly to the current quoted component."
            )
        return values
    weights = policy.get("weights", {}) if kind == "weighted" else {}
    weights = {person: weights.get(person, 1) for person in people}
    denominator = sum(weights.values())
    values = {person: total * weights[person] // denominator for person in people}
    remaining = total - sum(values.values())
    # Largest fractional remainder first, then stable canonical account identity.
    order = sorted(people, key=lambda p: (-(total * weights[p] % denominator), p))
    for person in order[:remaining]:
        values[person] += 1
    return values


def covers(proposed, required):
    return any(
        p["weekday"] == required["weekday"]
        and p["start_minute"] <= required["start_minute"]
        and p["end_minute"] >= required["end_minute"]
        for p in proposed
    )


def household_feasible(plan, person, values):
    if any(
        not covers(plan.get("quiet_windows", []), window)
        for window in values.get("quiet_windows", [])
    ):
        return False
    for task in plan.get("chores", []):
        if task["user_id"] != person:
            continue
        if task["id"] not in values.get("accepted_chore_ids", []):
            return False
        if any(
            window["weekday"] == task["weekday"]
            and window["start_minute"] < task["start_minute"] + task["duration_minutes"]
            and window["end_minute"] > task["start_minute"]
            for window in values.get("unavailable_windows", [])
        ):
            return False
    return True
