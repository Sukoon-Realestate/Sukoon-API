"""Exact bounded offer-subset search and a separate feasibility validator.

Money is minor-unit integer rent/deposit. A selected aggregate offer consumes
all of its physical scope, even when only some of its capacity is assigned.
"""

from itertools import combinations
from time import monotonic
from .assumptions import permitted, metrics

VERSION = "bounded-offer-subsets-v1"


def validate_plan(snapshot, plan):
    errors = []
    staff = {row["id"]: row for row in snapshot["staff"]}
    offers = {row["offer_id"]: row for row in snapshot["offers"]}
    chosen = plan.get("offer_ids", [])
    if len(chosen) != len(set(chosen)) or any(key not in offers for key in chosen):
        return ["invalid_offer_selection"]
    units, physical = {}, set()
    for key in chosen:
        for unit in offers[key]["units"]:
            keys = {(unit["id"], value) for value in unit["physical_keys"]}
            if physical & keys or unit["id"] in units:
                errors.append("physical_inventory_conflict")
            physical |= keys
            units[unit["id"]] = {**unit, "offer_id": key}
    assigned, counts = set(), {}
    for row in plan.get("assignments", []):
        person, unit = row.get("staff_id"), row.get("property_id")
        if person not in staff or person in assigned:
            errors.append("employee_coverage_invalid")
        assigned.add(person)
        if unit not in units or row.get("offer_id") != units.get(unit, {}).get(
            "offer_id"
        ):
            errors.append("assignment_scope_invalid")
            continue
        counts[unit] = counts.get(unit, 0) + 1
        allowed = snapshot["constraints"].get("allowed_property_ids", {}).get(person)
        if allowed is not None and unit not in allowed:
            errors.append("employee_location_constraint")
        if not permitted(snapshot, person, unit):
            errors.append("commute_or_unavailable_constraint")
    if assigned != set(staff):
        errors.append("required_employee_unassigned")
    if any(count > units[unit]["capacity"] for unit, count in counts.items()):
        errors.append("capacity_exceeded")
    for key in chosen:
        offer = offers[key]
        if offer.get(
            "occupancy_policy", "reserve_capacity_with_notice"
        ) != "reserve_capacity_with_notice" and sum(
            counts.get(unit["id"], 0) for unit in offer["units"]
        ) != sum(
            unit["capacity"] for unit in offer["units"]
        ):
            errors.append("named_occupants_required")
    monthly = sum(offers[key]["monthly_rent"]["amount_minor"] for key in chosen)
    rent = monthly * snapshot["months"]
    deposit = sum(offers[key]["deposit"]["amount_minor"] for key in chosen)
    if rent > snapshot["constraints"]["rent_limit_minor"]:
        errors.append("rent_limit_exceeded")
    if deposit > snapshot["constraints"]["deposit_limit_minor"]:
        errors.append("deposit_limit_exceeded")
    if (
        plan.get("full_term_rent_minor"),
        plan.get("deposit_minor"),
        plan.get("monthly_rent_minor"),
    ) != (rent, deposit, monthly):
        errors.append("cost_mismatch")
    return sorted(set(errors))


def _assignment(snapshot, selected):
    slots, required = [], []
    for offer in selected:
        for unit in offer["units"]:
            must_fill = (
                offer.get("occupancy_policy", "reserve_capacity_with_notice")
                != "reserve_capacity_with_notice"
            )
            if must_fill and unit["capacity"] > len(snapshot["staff"]):
                return None
            # The allocation only needs as many slots as employees, avoiding
            # unbounded work from a corrupt or extremely large capacity value.
            start = len(slots)
            slots.extend(
                (offer["offer_id"], unit["id"])
                for _ in range(min(unit["capacity"], len(snapshot["staff"])))
            )
            if must_fill:
                required.extend(range(start, len(slots)))
    occupants = {}
    allowed = snapshot["constraints"].get("allowed_property_ids", {})

    # First saturate the mandatory named-occupant slots. Then extend this
    # matching to every employee without ever un-filling a required slot.
    by_person = {}

    def fill_required(index, seen):
        unit = slots[index][1]
        for staff in snapshot["staff"]:
            person = staff["id"]
            if (
                person in seen
                or (person in allowed and unit not in allowed[person])
                or not permitted(snapshot, person, unit)
            ):
                continue
            seen.add(person)
            if person not in by_person or fill_required(by_person[person], seen):
                by_person[person] = index
                return True
        return False

    for index in required:
        if not fill_required(index, set()):
            return None
    occupants = {index: person for person, index in by_person.items()}

    def place(person, seen):
        for index, (_, unit) in enumerate(slots):
            if (
                index in seen
                or (person in allowed and unit not in allowed[person])
                or not permitted(snapshot, person, unit)
            ):
                continue
            seen.add(index)
            if index not in occupants or place(occupants[index], seen):
                occupants[index] = person
                return True
        return False

    for staff in snapshot["staff"]:
        if staff["id"] in by_person:
            continue
        if not place(staff["id"], set()):
            return None
    return sorted(
        [
            {
                "staff_id": person,
                "property_id": slots[index][1],
                "offer_id": slots[index][0],
                "placement_status": "proposed",
            }
            for index, person in occupants.items()
        ],
        key=lambda row: row["staff_id"],
    )


def solve(snapshot, *, max_subsets=4096, max_seconds=1.5, cancelled=lambda: False):
    started, visited, completed = monotonic(), 0, True
    best_rent, best_deposit = None, None
    offers = snapshot["offers"]
    for size in range(1, len(offers) + 1):
        for chosen in combinations(offers, size):
            if (
                visited >= max_subsets
                or monotonic() - started >= max_seconds
                or (visited % 32 == 0 and cancelled())
            ):
                completed = False
                break
            visited += 1
            unit_ids = [unit["id"] for row in chosen for unit in row["units"]]
            if len(unit_ids) != len(set(unit_ids)):
                continue
            monthly = sum(row["monthly_rent"]["amount_minor"] for row in chosen)
            deposit = sum(row["deposit"]["amount_minor"] for row in chosen)
            if (
                monthly * snapshot["months"]
                > snapshot["constraints"]["rent_limit_minor"]
                or deposit > snapshot["constraints"]["deposit_limit_minor"]
            ):
                continue
            if sum(unit["capacity"] for row in chosen for unit in row["units"]) < len(
                snapshot["staff"]
            ):
                continue
            assigned = _assignment(snapshot, chosen)
            if assigned is None:
                continue
            candidate = {
                "offer_ids": sorted(row["offer_id"] for row in chosen),
                "assignments": assigned,
                "employees_allocated": len(assigned),
                "employees_unallocated": 0,
                "monthly_rent_minor": monthly,
                "full_term_rent_minor": monthly * snapshot["months"],
                "deposit_minor": deposit,
                "commute": {
                    "status": "unknown",
                    "source": None,
                    "estimated_minutes": None,
                },
                "baseline_occupancy": "not_established",
                "proposed_move_count": None,
            }
            candidate.update(metrics(snapshot, assigned))
            known_costs = [
                candidate.get("estimated_transport_minor"),
                candidate.get("estimated_moving_minor"),
                candidate.get("estimated_turnover_minor"),
            ]
            candidate["estimated_known_expense_minor"] = candidate[
                "full_term_rent_minor"
            ] + sum(x for x in known_costs if x is not None)
            candidate["expense_complete"] = False
            candidate["explanation"] = {
                "satisfied": [
                    "required_coverage",
                    "capacity",
                    "physical_scope",
                    "location_policy",
                    "rent_limit",
                    "deposit_limit",
                    "commute_limit",
                ],
                "unknown": ["moving_count", "shift_accurate_route"],
                "baseline_changed": "not_proven",
                "policy_version": "corporate-assumptions-v2",
            }
            if validate_plan(snapshot, candidate):
                continue
            rent_order = (
                candidate["full_term_rent_minor"],
                deposit,
                len(chosen),
                candidate["offer_ids"],
            )
            deposit_order = (
                deposit,
                candidate["full_term_rent_minor"],
                len(chosen),
                candidate["offer_ids"],
            )
            if best_rent is None or rent_order < best_rent[0]:
                best_rent = rent_order, candidate
            if best_deposit is None or deposit_order < best_deposit[0]:
                best_deposit = deposit_order, candidate
        if not completed:
            break
    plans = []
    for label, entry in (("lowest_rent", best_rent), ("lowest_deposit", best_deposit)):
        if entry is not None:
            plans.append(
                {
                    **entry[1],
                    "id": label,
                    "objective": label,
                    "optimality_proven": completed,
                    "independent_validation": "passed",
                }
            )
    return {
        "result_status": (
            ("optimal" if completed else "feasible")
            if plans
            else ("infeasible" if completed else "unknown")
        ),
        "optimality_proven": completed and bool(plans),
        "search_complete": completed,
        "subsets_examined": visited,
        "solver_version": VERSION,
        "plan_options": plans,
        "employees_unallocated": 0 if plans else len(snapshot["staff"]),
        "reason_codes": (
            []
            if plans
            else [
                (
                    "bounded_capacity_location_or_budget_conflict"
                    if completed
                    else "computation_limit"
                )
            ]
        ),
        "scope": "selected_inventory_and_dates_only",
        "execution_available": False,
        "blocking_reason_codes": ["decision_and_canonical_approval_required"],
    }
