"""Deterministic bounded enumeration, with no probing of arbitrary prices."""

from collections import Counter
from itertools import product
import hashlib
import json
import uuid

from rest_framework.exceptions import ValidationError
from ..planning import display_name, offer_money, selection
from ..rental_lifecycle.inventory import assert_available, unit_keys
from ..rental_phase2 import RentalConflict
from . import policies

MAX_ASSIGNMENTS = 4096
MAX_CANDIDATES = 3
PURPOSE_VERSION = "living-lab-private-v1"


def equal_shares(total, people):
    """First sorted canonical account IDs receive one remaining minor unit."""
    ordered = sorted(people)
    share, remainder = divmod(total, len(ordered))
    return {person: share + (index < remainder) for index, person in enumerate(ordered)}


def canonical_inventory(request, lab, *, lock=True):
    prop, snapshot = selection(request, lab.selection, lock=lock)
    if snapshot != lab.selection:
        raise RentalConflict(
            "The selected quote changed. Start a fresh reviewed lab.",
            code="source_changed",
        )
    assert_available(prop, snapshot, lab.starts_on, lab.ends_on_exclusive)
    if type(snapshot.get("capacity")) is not int or snapshot["capacity"] < len(
        policies.participants(lab)
    ):
        raise ValidationError(
            {"selection": "The explicit offer capacity must cover every participant."}
        )
    inventory = prop.rental_inventory or {}
    all_rooms = inventory.get("rooms", [])
    rooms = (
        all_rooms
        if snapshot["rental_scope"] == "entire_property"
        else [room for room in all_rooms if str(room.get("id")) in snapshot["room_ids"]]
    )
    if snapshot["rental_scope"] not in {"entire_property", "room_group", "room"}:
        raise ValidationError(
            {
                "selection": "Choose an entire property, room group, or room for shared planning."
            }
        )
    if (
        not rooms
        or len(rooms) > policies.limit("MAX_ROOMS", 6)
        or any(
            not room.get("id")
            or type(room.get("capacity")) is not int
            or not 1 <= room["capacity"] <= policies.limit("MAX_PARTICIPANTS", 6)
            for room in rooms
        )
    ):
        raise ValidationError(
            {
                "selection": "Use explicit room capacities within the configured planning limits."
            }
        )
    rent, deposit = offer_money(snapshot)
    if deposit is None:
        raise ValidationError(
            {
                "selection": "The owner must specify deposit terms before this calculation."
            }
        )
    return (
        snapshot,
        sorted(
            [
                {
                    "id": str(room["id"]),
                    "name": str(room.get("name") or ""),
                    "capacity": room["capacity"],
                }
                for room in rooms
            ],
            key=lambda room: room["id"],
        ),
        rent,
        deposit,
        unit_keys(prop, snapshot),
    )


def input_digest(lab, rows, rooms):
    # Stored only server-side. Do not return a digest of low-entropy private limits.
    value = {
        "selection": lab.selection,
        "periods": lab.participant_periods,
        "input_revision": lab.input_revision,
        "public_revision": lab.public_revision,
        "allocation_policy": lab.allocation_policy,
        "household_plan": lab.household_plan,
        "scenario": lab.scenario,
        "rooms": rooms,
        "requirements": [
            {
                "user": str(row.user.id),
                "revision": row.revision,
                "status": row.status,
                "values": row.private_values,
            }
            for row in rows
        ],
    }
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def require_run_current(run, lab, rooms):
    rows = list(lab.requirements.select_related("user").order_by("user__id"))
    if run.input_revision != lab.input_revision or run.input_digest != input_digest(
        lab, rows, rooms
    ):
        raise RentalConflict(
            "The room map or private input snapshot changed.", code="source_changed"
        )


def solve(lab, rows, rooms, rent, deposit, physical_keys):
    people = policies.participants(lab)
    requirements = {str(row.user.id): row for row in rows}
    if not set(people).issubset(requirements) or any(
        requirements[person].status != "provided"
        or requirements[person].purpose_version != PURPOSE_VERSION
        or requirements[person].public_revision != lab.public_revision
        for person in people
    ):
        return "invalid_input", "inputs_incomplete", [], 0
    rents = policies.shares(rent, people, lab.allocation_policy, "rent")
    deposits = policies.shares(deposit, people, lab.allocation_policy, "deposit")
    expense = lab.household_plan.get("expense_minor", 0)
    expenses = policies.shares(expense, people, lab.allocation_policy, "expense")
    limits = {person: requirements[person].private_values for person in people}
    for person, values in limits.items():
        if expense and values.get("expense_max_minor") is None:
            return "invalid_input", "inputs_incomplete", [], 0
        if (
            rents[person] > values["rent_max_minor"]
            or deposits[person] > values["deposit_max_minor"]
            or values["accepted_start_on"] > str(lab.starts_on)
            or values["accepted_end_on"] < str(lab.ends_on_exclusive)
            or (expense and expenses[person] > values["expense_max_minor"])
            or not policies.household_feasible(lab.household_plan, person, values)
        ):
            return "infeasible", "no_workable_arrangement", [], 0
    rooms = [
        room
        for room in rooms
        if room["id"] not in lab.scenario.get("unavailable_room_ids", [])
    ]
    capacity = {room["id"]: room["capacity"] for room in rooms}
    room_names = {room["id"]: room["name"] for room in rooms}
    options = [
        [
            room["id"]
            for room in rooms
            if not limits[person]["required_room_id"]
            or room["id"] == limits[person]["required_room_id"]
        ]
        for person in people
    ]
    candidates, examined = [], 0
    for assignment in product(*options):
        if examined >= MAX_ASSIGNMENTS:
            return (
                ("feasible", "bounded_candidates", candidates, examined)
                if candidates
                else ("unknown", "computation_limit", [], examined)
            )
        examined += 1
        occupancy = Counter(assignment)
        if any(count > capacity[room] for room, count in occupancy.items()):
            continue
        if any(
            limits[person]["private_room"] and occupancy[assignment[index]] != 1
            for index, person in enumerate(people)
        ):
            continue
        candidates.append(
            {
                "id": str(uuid.uuid4()),
                "policy": lab.allocation_policy.get("kind", "equal"),
                "policy_version": policies.VERSION,
                "allocation_policy": lab.allocation_policy,
                "remainder_rule": "largest_fraction_then_ascending_account_id",
                "starts_on": str(lab.starts_on),
                "ends_on_exclusive": str(lab.ends_on_exclusive),
                "selection": lab.selection,
                "price_period": lab.selection["terms"]["price_period"],
                "physical_keys": physical_keys,
                "house_rules": lab.house_rules,
                "household_plan": lab.household_plan,
                "scenario": lab.scenario,
                "obligations_unchanged": True,
                "public_revision": lab.public_revision,
                "rent_total": {"amount_minor": rent, "currency": "EGP", "exponent": 2},
                "deposit_total": {
                    "amount_minor": deposit,
                    "currency": "EGP",
                    "exponent": 2,
                },
                "expense_total": {
                    "amount_minor": expense,
                    "currency": "EGP",
                    "exponent": 2,
                },
                "shares": [
                    {
                        "user_id": person,
                        "user_name": display_name(requirements[person].user),
                        "room_id": assignment[index],
                        "room_name": room_names[assignment[index]],
                        "rent_minor": rents[person],
                        "deposit_minor": deposits[person],
                        "expense_minor": expenses[person],
                    }
                    for index, person in enumerate(people)
                ],
                "planning_only": True,
                "inventory_reserved": False,
                "lease_amendment_authorized": False,
            }
        )
        if len(candidates) == MAX_CANDIDATES:
            break
    return (
        ("feasible", "bounded_candidates", candidates, examined)
        if candidates
        else ("infeasible", "no_workable_arrangement", [], examined)
    )
