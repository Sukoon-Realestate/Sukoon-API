"""Versioned declared assumptions and deterministic mock travel, never real routes."""

import math
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from config.advanced_housing import require_mock_mode
from core_apps.properties.models import Property

VERSION = "corporate-assumptions-v2"


def capture(user, data, staff_ids, unit_ids):
    raw = data.get("planning_assumptions", {})
    if not raw:
        return {}
    require_mock_mode()
    if not isinstance(raw, dict) or set(raw) - {
        "site_name",
        "latitude",
        "longitude",
        "shift_label",
        "mode",
        "rationale",
        "transport_monthly_minor",
        "moving_per_person_minor",
        "turnover_per_unit_minor",
        "max_commute_minutes",
        "unavailable_property_ids",
    }:
        raise ValidationError(
            {
                "planning_assumptions": "Use the supported versioned planning assumptions."
            }
        )
    result = {
        "policy_version": VERSION,
        "owner_id": str(user.id),
        "provenance": "coordinator_declared",
        "provider": "mock_haversine_v2",
        "simulated": True,
    }
    for key, limit in (("site_name", 160), ("shift_label", 120), ("rationale", 1000)):
        value = raw.get(key, "")
        if not isinstance(value, str) or len(value) > limit:
            raise ValidationError({key: "Supply a bounded text assumption."})
        result[key] = value.strip()
    if not result["rationale"]:
        raise ValidationError(
            {"rationale": "Explain the declared work site and cost assumptions."}
        )
    for key, bound in (("latitude", 90), ("longitude", 180)):
        value = raw.get(key)
        if value in (None, ""):
            result[key] = None
            continue
        if isinstance(value, bool):
            raise ValidationError(
                {key: "Supply valid coordinates or leave them unknown."}
            )
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(
                {key: "Supply valid coordinates or leave them unknown."}
            )
        if not math.isfinite(value) or abs(value) > bound:
            raise ValidationError(
                {key: "Supply valid coordinates or leave them unknown."}
            )
        result[key] = value
    result["mode"] = raw.get("mode", "driving")
    if result["mode"] not in {"driving", "walking", "cycling", "transit"}:
        raise ValidationError({"mode": "Choose a supported transport assumption."})
    for key in (
        "transport_monthly_minor",
        "moving_per_person_minor",
        "turnover_per_unit_minor",
    ):
        value = raw.get(key)
        if value is not None and (
            type(value) is not int or not 0 <= value <= 99999999999
        ):
            raise ValidationError(
                {
                    key: "Supply a nonnegative estimate in minor units or leave it unknown."
                }
            )
        result[key] = value
    value = raw.get("max_commute_minutes")
    if value is not None and (type(value) is not int or not 1 <= value <= 360):
        raise ValidationError(
            {
                "max_commute_minutes": "Choose a per-person commute limit from 1 to 360 minutes."
            }
        )
    result["max_commute_minutes"] = value
    unavailable = raw.get("unavailable_property_ids", [])
    if (
        not isinstance(unavailable, list)
        or any(not isinstance(x, str) for x in unavailable)
        or set(unavailable) - unit_ids
    ):
        raise ValidationError(
            {
                "unavailable_property_ids": "Choose canonical selected properties for the unavailable scenario."
            }
        )
    result["unavailable_property_ids"] = sorted(set(unavailable))
    result["routes"] = {}
    for prop in Property.objects.filter(id__in=unit_ids):
        minutes = None
        if None not in (
            result["latitude"],
            result["longitude"],
            prop.latitude,
            prop.longitude,
        ):
            lat1, lat2 = math.radians(float(prop.latitude)), math.radians(
                result["latitude"]
            )
            dlat, dlon = lat2 - lat1, math.radians(
                result["longitude"] - float(prop.longitude)
            )
            distance = (
                6371
                * 2
                * math.asin(
                    min(
                        1,
                        math.sqrt(
                            math.sin(dlat / 2) ** 2
                            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
                        ),
                    )
                )
            )
            speed = {"driving": 30, "walking": 4, "cycling": 12, "transit": 20}[
                result["mode"]
            ]
            minutes = math.ceil(distance * 1.35 / speed * 60)
        result["routes"][str(prop.id)] = {
            "minutes": minutes,
            "status": "mock_estimate" if minutes is not None else "unknown",
            "provider": "mock_haversine_v2",
            "timing": "shift_specific_routing_unsupported",
            "origin_revision": (prop.rental_inventory or {}).get("revision", 0),
        }
    return result


def source_data(value):
    return {
        key: value[key]
        for key in (
            "site_name",
            "latitude",
            "longitude",
            "shift_label",
            "mode",
            "rationale",
            "transport_monthly_minor",
            "moving_per_person_minor",
            "turnover_per_unit_minor",
            "max_commute_minutes",
            "unavailable_property_ids",
        )
        if key in value
    }


def permitted(snapshot, person, unit):
    assumptions = snapshot.get("planning_assumptions", {})
    if unit in assumptions.get("unavailable_property_ids", []):
        return False
    maximum = assumptions.get("max_commute_minutes")
    minutes = assumptions.get("routes", {}).get(unit, {}).get("minutes")
    return maximum is None or (minutes is not None and minutes <= maximum)


def metrics(snapshot, assignments):
    assumption = snapshot.get("planning_assumptions", {})
    values = [
        assumption.get("routes", {}).get(row["property_id"], {}).get("minutes")
        for row in assignments
    ]
    known = bool(values) and all(v is not None for v in values)
    people = [
        {
            "staff_id": row["staff_id"],
            "property_id": row["property_id"],
            "minutes": value,
        }
        for row, value in zip(assignments, values)
    ]
    transport = assumption.get("transport_monthly_minor")
    turnover = assumption.get("turnover_per_unit_minor")
    moving = assumption.get("moving_per_person_minor")
    return {
        "commute": {
            "status": "mock_estimate" if known else "unknown",
            "source": assumption.get("provider"),
            "timing": "shift_specific_routing_unsupported",
            "average_minutes": round(sum(values) / len(values), 1) if known else None,
            "maximum_minutes": max(values) if known else None,
            "distribution": people,
            "simulated": bool(assumption),
        },
        "estimated_transport_minor": (
            transport * snapshot["months"] if transport is not None else None
        ),
        "estimated_turnover_minor": (
            turnover * len({row["property_id"] for row in assignments})
            if turnover is not None
            else None
        ),
        "estimated_moving_minor": (
            moving * len(assignments) if moving is not None else None
        ),
        "moving_cost_basis": "one_hypothetical_arrival_per_selected_person",
        "planned_arrival_count": len(assignments),
        "proposed_move_count": None,
        "baseline_occupancy": "not_established",
        "estimate_provenance": "coordinator_declared_mock_routes",
        "assumption_count": len(assumption) if assumption else 0,
    }
