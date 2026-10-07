import copy
import uuid
from decimal import Decimal, InvalidOperation

from rest_framework.exceptions import ValidationError


SCOPES = {"entire_property", "room", "room_group", "bed"}
AVAILABILITY = {"available", "unavailable", "rented"}
INHERITABLE = {
    "rental_period",
    "deposit",
    "suitable_for",
    "description",
    "smoking_allowed",
    "rules",
}


def _new_id():
    return str(uuid.uuid4())


def _resolve_id(item, old_by_id, client_map):
    supplied_id = str(item.get("id") or "")
    client_key = str(item.get("client_key") or "")
    if supplied_id:
        if supplied_id not in old_by_id:
            raise ValidationError(
                "An existing inventory ID does not belong to this property."
            )
        return supplied_id
    if not client_key:
        raise ValidationError("New inventory entities require client_key.")
    if client_key in client_map:
        raise ValidationError("Duplicate client_key in rental_inventory.")
    assigned = _new_id()
    client_map[client_key] = assigned
    return assigned


def normalize_inventory(value, existing=None):
    if isinstance(value, str):
        import json

        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            raise ValidationError({"rental_inventory": "Must be valid JSON."})
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValidationError({"rental_inventory": "schema_version 1 is required."})
    mode = value.get("mode")
    if mode not in {"whole", "partial"}:
        raise ValidationError({"rental_inventory": "mode must be whole or partial."})
    existing = existing or {}
    current_revision = int(existing.get("revision", 0))
    if int(value.get("expected_revision", 0)) != current_revision:
        raise ValidationError(
            {
                "rental_inventory": f"inventory_revision_conflict: current revision is {current_revision}."
            }
        )

    output = copy.deepcopy(value)
    client_map = {}
    old_rooms = {
        str(item.get("id")): item
        for item in existing.get("rooms", [])
        if item.get("id")
    }
    old_beds = {
        str(item.get("id")): item
        for room in existing.get("rooms", [])
        for item in room.get("beds", [])
        if item.get("id")
    }
    old_offers = {
        str(item.get("id")): item
        for item in existing.get("offers", [])
        if item.get("id")
    }
    rooms_by_id = {}
    beds_by_id = {}

    for room in output.get("rooms", []):
        room["id"] = _resolve_id(room, old_rooms, client_map)
        room.setdefault("client_key", "")
        if not str(room.get("name") or "").strip():
            raise ValidationError({"rental_inventory": "Every room requires a name."})
        capacity = room.get("capacity")
        if capacity is not None and (not isinstance(capacity, int) or capacity < 1):
            raise ValidationError(
                {
                    "rental_inventory": "Room capacity must be a positive integer or null."
                }
            )
        room_beds = []
        for bed in room.get("beds", []):
            bed["id"] = _resolve_id(bed, old_beds, client_map)
            bed.setdefault("client_key", "")
            if not str(bed.get("name") or "").strip():
                raise ValidationError(
                    {"rental_inventory": "Every bed requires a name."}
                )
            bed["room_id"] = room["id"]
            beds_by_id[bed["id"]] = bed
            room_beds.append(bed)
        if capacity is not None and len(room_beds) > capacity:
            raise ValidationError(
                {"rental_inventory": "Identified beds cannot exceed room capacity."}
            )
        room["beds"] = room_beds
        rooms_by_id[room["id"]] = room

    shared_defaults = output.get("shared_defaults") or {}
    output["shared_defaults"] = shared_defaults
    allocations = set()
    normalized_offers = []
    for offer in output.get("offers", []):
        offer["id"] = _resolve_id(offer, old_offers, client_map)
        offer.setdefault("client_key", "")
        scope = offer.get("rental_scope")
        if scope not in SCOPES:
            raise ValidationError({"rental_inventory": "Unsupported rental_scope."})
        if offer.get("availability", "available") not in AVAILABILITY:
            raise ValidationError({"rental_inventory": "Unsupported availability."})
        room_ids = [
            client_map.get(str(item), str(item)) for item in offer.get("room_ids", [])
        ]
        bed_id = (
            client_map.get(str(offer.get("bed_id")), str(offer.get("bed_id")))
            if offer.get("bed_id")
            else None
        )
        if any(room_id not in rooms_by_id for room_id in room_ids):
            raise ValidationError(
                {
                    "rental_inventory": "Offer contains a foreign or unknown room reference."
                }
            )
        if scope == "entire_property" and (room_ids or bed_id):
            raise ValidationError(
                {
                    "rental_inventory": "Entire-property offers cannot reference rooms or beds."
                }
            )
        if scope in {"room", "bed"} and len(room_ids) != 1:
            raise ValidationError(
                {"rental_inventory": "Room and bed offers require exactly one room."}
            )
        if scope == "room_group" and len(set(room_ids)) < 2:
            raise ValidationError(
                {"rental_inventory": "Room groups require at least two distinct rooms."}
            )
        if scope == "bed":
            if bed_id not in beds_by_id or beds_by_id[bed_id]["room_id"] != room_ids[0]:
                raise ValidationError(
                    {"rental_inventory": "Bed does not belong to the referenced room."}
                )
            if ("bed", bed_id) in allocations or ("room", room_ids[0]) in allocations:
                raise ValidationError({"rental_inventory": "inventory_overlap"})
            allocations.add(("bed", bed_id))
        elif scope in {"room", "room_group"}:
            for room_id in room_ids:
                if ("room", room_id) in allocations or any(
                    key[0] == "bed"
                    and beds_by_id.get(key[1], {}).get("room_id") == room_id
                    for key in allocations
                ):
                    raise ValidationError({"rental_inventory": "inventory_overlap"})
                allocations.add(("room", room_id))
        terms = offer.get("term_overrides") or offer.get("terms") or {}
        inherited = set(offer.get("inherited_fields", []))
        if not inherited.issubset(INHERITABLE) or inherited.intersection(terms):
            raise ValidationError(
                {"rental_inventory": "Invalid or conflicting inherited_fields."}
            )
        resolved = {key: shared_defaults.get(key) for key in inherited}
        resolved.update(terms)
        try:
            if Decimal(str(resolved.get("price"))) < 0:
                raise InvalidOperation
        except (InvalidOperation, TypeError):
            raise ValidationError(
                {
                    "rental_inventory": "Every offer requires a non-negative decimal price."
                }
            )
        if resolved.get("price_period") not in {"daily", "weekly", "monthly", "yearly"}:
            raise ValidationError(
                {"rental_inventory": "Every offer requires a valid price_period."}
            )
        offer["room_ids"] = room_ids
        if bed_id:
            offer["bed_id"] = bed_id
        offer["terms"] = resolved
        offer.pop("term_overrides", None)
        offer["inherited_fields"] = sorted(inherited)
        offer.setdefault("availability", "available")
        offer.setdefault("archived", False)
        old_revision = int(old_offers.get(offer["id"], {}).get("revision", 0))
        offer["revision"] = old_revision + 1
        offer["offer_link"] = ""
        offer["actions"] = {"can_archive": True, "can_set_availability": True}
        normalized_offers.append(offer)

    if mode == "whole" and (
        len([o for o in normalized_offers if not o["archived"]]) != 1
        or normalized_offers[0]["rental_scope"] != "entire_property"
    ):
        raise ValidationError(
            {
                "rental_inventory": "Whole mode requires exactly one active entire-property offer."
            }
        )
    if mode == "partial" and any(
        o["rental_scope"] == "entire_property" and not o["archived"]
        for o in normalized_offers
    ):
        raise ValidationError(
            {
                "rental_inventory": "Partial mode cannot contain an active entire-property offer."
            }
        )
    output["rooms"] = list(rooms_by_id.values())
    output["offers"] = normalized_offers
    output["revision"] = current_revision + 1
    output.pop("expected_revision", None)
    return output
